"""Conservative AST alpha-only diagnostic, NOT a general semantic-equivalence proof."""
import ast
import hashlib
import json
from pathlib import Path

class Unsupported(ValueError):
    pass

ALLOWED = {
    "Module","FunctionDef","arguments","arg","Assign","AugAssign","For","While","If",
    "Return","Break","Continue","Pass","Expr","Name","Load","Store","Constant","List",
    "Tuple","Set","Dict","Subscript","Slice","Attribute","Call","keyword","BinOp",
    "UnaryOp","BoolOp","Compare","IfExp","Add","Sub","Mult","Div","FloorDiv","Mod",
    "Pow","BitOr","BitAnd","BitXor","LShift","RShift","UAdd","USub","Not","Invert",
    "And","Or","Eq","NotEq","Lt","LtE","Gt","GtE","Is","IsNot","In","NotIn"
}
BUILTINS = {"len","list","dict","set","tuple","range","enumerate","sorted","min","max",
            "sum","all","any","zip","bool","int","str","abs","reversed"}
METHODS = {"append","extend","pop","remove","add","discard","items","keys","values",
           "get","copy","sort","index","count","update","setdefault","clear"}
PUBLIC_ARGS = ("tasks","dependencies")

def canonical(source):
    if not isinstance(source,str) or len(source.encode("utf-8"))>40000:
        raise Unsupported("source budget/type")
    tree=ast.parse(source)
    nodes=list(ast.walk(tree))
    if len(nodes)>5000:raise Unsupported("AST budget")
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.type_ignores:
        raise Unsupported("one function only")
    fn=tree.body[0];a=fn.args
    if (fn.name!="order_tasks" or tuple(x.arg for x in a.args)!=PUBLIC_ARGS
        or a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg or a.defaults or a.kw_defaults
        or fn.decorator_list or fn.returns or fn.type_comment or getattr(fn,"type_params",())
        or any(x.annotation or x.type_comment for x in a.args)):
        raise Unsupported("public signature/decorators/annotations")
    for node in nodes:
        if type(node).__name__ not in ALLOWED:
            raise Unsupported("unsupported syntax: "+type(node).__name__)
        if isinstance(node,ast.FunctionDef) and node is not fn:
            raise Unsupported("nested scope")
        if isinstance(node,(ast.Assign,ast.For)) and node.type_comment:
            raise Unsupported("type comment")
        if isinstance(node,ast.Name) and node.id.startswith("__"):
            raise Unsupported("dunder name")
        if isinstance(node,ast.Attribute) and node.attr.startswith("__"):
            raise Unsupported("dunder attribute")
        if isinstance(node,ast.keyword) and node.arg is None:
            raise Unsupported("keyword expansion")
        if isinstance(node,ast.Dict) and any(k is None for k in node.keys):
            raise Unsupported("dictionary expansion")
    bindings=sorted((n for n in nodes if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)),
                    key=lambda n:(n.lineno,n.col_offset))
    local=[]
    for node in bindings:
        if node.id not in PUBLIC_ARGS and node.id not in local:local.append(node.id)
    if "order_tasks" in local or any(x in BUILTINS for x in local):
        raise Unsupported("shadowed public/builtin callable")
    # Resolve bindings for the ENTIRE function, including reads before a later assignment.
    for node in nodes:
        if isinstance(node,ast.Call):
            f=node.func
            if isinstance(f,ast.Name):
                if f.id not in BUILTINS or f.id in local:
                    raise Unsupported("unreviewed or locally bound callable")
            elif not isinstance(f,ast.Attribute) or f.attr not in METHODS:
                raise Unsupported("unreviewed method/call target")
    mapping={name:"$local:"+str(i) for i,name in enumerate(local)}
    class Rename(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id in mapping:node.id=mapping[node.id]
            return node
    Rename().visit(tree)
    return ast.dump(tree,annotate_fields=True,include_attributes=False)

def compare(left,right):
    def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
    result={"left_sha256":sha(left),"right_sha256":sha(right),
            "scope":"Restricted AST alpha-renaming only; not universal semantic equivalence."}
    try:
        a,b=canonical(left),canonical(right)
    except (Unsupported,SyntaxError,ValueError,RecursionError,MemoryError) as e:
        return {**result,"classification":"UNKNOWN","reason":str(e)}
    return {**result,"classification":"ALPHA_ONLY_MATCH" if a==b else "DIFFERENT"}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("left");p.add_argument("right");args=p.parse_args()
    print(json.dumps(compare(Path(args.left).read_text(),Path(args.right).read_text()),indent=2))
