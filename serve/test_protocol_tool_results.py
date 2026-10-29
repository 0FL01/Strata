import unittest
import copy,itertools
from serve.frontend import anthropic_to_messages
from serve.responses import _order_tool_results
class ProtocolOrder(unittest.TestCase):
 def test_anthropic_reversed_results(self):
  req={'messages':[{'role':'assistant','content':[{'type':'tool_use','id':c,'name':'read','input':{'path':c}} for c in ('a','b')]},
       {'role':'user','content':[{'type':'tool_result','tool_use_id':c,'content':'result-'+c} for c in ('b','a')]}]}
  old=copy.deepcopy(req);msgs,_,_=anthropic_to_messages(req)
  self.assertEqual([m['content'] for m in msgs if m['role']=='tool'],['result-a','result-b'])
  self.assertEqual(req,old);self.assertNotIn('_call_id',str(msgs))
 def test_responses_invalid_ids_do_not_crash_or_reorder(self):
  for bad in ([],{},True,1,None,''):
   with self.subTest(bad=bad):
    msgs=[{'role':'assistant','tool_calls':[{'_call_id':bad,'function':{}},{'_call_id':'b','function':{}}]},
          {'role':'tool','_call_id':'b','content':'B'},{'role':'tool','_call_id':bad,'content':'A'}]
    _order_tool_results(msgs)
    self.assertEqual([m['content'] for m in msgs if m['role']=='tool'],['B','A'])
    self.assertNotIn('_call_id',str(msgs))
 def test_responses_complete_permutations(self):
  for order in itertools.permutations(('a','b','c')):
   msgs=[{'role':'assistant','tool_calls':[{'_call_id':c,'function':{}} for c in ('a','b','c')]}]
   msgs += [{'role':'tool','_call_id':c,'content':c} for c in order]
   _order_tool_results(msgs)
   self.assertEqual([m['content'] for m in msgs if m['role']=='tool'],['a','b','c'])
 def test_responses_partial_unknown_preserves_order(self):
  for ids in [('b','unknown'),('unknown','b'),('b','b'),('b',)]:
   msgs=[{'role':'assistant','tool_calls':[{'_call_id':c,'function':{}} for c in ('a','b')]}]
   msgs += [{'role':'tool','_call_id':c,'content':c} for c in ids]
   _order_tool_results(msgs);self.assertEqual([m['content'] for m in msgs if m['role']=='tool'],list(ids))

class ProtocolMatrix(unittest.TestCase):
 def convert(self, protocol, calls, results, tail=False):
  if protocol == 'anthropic':
   req={'messages':[{'role':'assistant','content':[{'type':'tool_use','id':cid,'name':'read','input':{'_call_id':'argument-kept','nested':{'x':cid}}} for cid in calls]},
    {'role':'user','content':[{'type':'tool_result','tool_use_id':cid,'content':content} for cid,content in results]+([{'type':'text','text':'after-results'}] if tail else [])}]}
   original=copy.deepcopy(req); out=anthropic_to_messages(req)[0]
  else:
   from serve.responses import input_messages
   req={'input':[{'type':'function_call','call_id':cid,'name':'read','namespace':'fs','arguments':{'_call_id':'argument-kept','nested':{'x':cid}}} for cid in calls]+
    [{'type':'function_call_output','call_id':cid,'output':content} for cid,content in results]+([{'role':'user','content':'after-results'}] if tail else [])}
   original=copy.deepcopy(req);out=input_messages(req)
  self.assertEqual(req,original)
  for message in out:
   self.assertNotIn('_call_id',message)
   for call in message.get('tool_calls',[]):
    self.assertNotIn('_call_id',call)
    self.assertEqual(call['function']['arguments']['_call_id'],'argument-kept')
  return out
 def test_all_protocol_permutations(self):
  for protocol in ('anthropic','responses'):
   for order in itertools.permutations(('a','b','c')):
    with self.subTest(protocol=protocol,order=order):
     out=self.convert(protocol,['a','b','c'],[(c,c) for c in order],True)
     self.assertEqual([m['content'] for m in out if m['role']=='tool'],['a','b','c'])
     self.assertEqual(out[-1],{'role':'user','content':'after-results'})
 def test_ambiguous_sets_preserve_received_order(self):
  for protocol in ('anthropic','responses'):
   for calls,ids in [(['a','b','c'],['c','a']),(['a','b'],['b','x']),(['a','b'],['b','b']),(['a','a'],['a','a'])]:
    with self.subTest(protocol=protocol,calls=calls,ids=ids):
     out=self.convert(protocol,calls,[(c,'result-'+str(i)) for i,c in enumerate(ids)])
     self.assertEqual([m['content'] for m in out if m['role']=='tool'],['result-'+str(i) for i in range(len(ids))])
 def test_invalid_ids_at_converter_boundary(self):
  for protocol in ('anthropic','responses'):
   for bad in (None,'',True,1,[],{}):
    with self.subTest(protocol=protocol,bad=bad):
     out=self.convert(protocol,[bad,'b'],[('b','B'),(bad,'A')])
     self.assertEqual([m['content'] for m in out if m['role']=='tool'],['B','A'])
 def test_multimodal_result_moves_intact(self):
  for protocol in ('anthropic','responses'):
   if protocol=='anthropic':
    image={'type':'image','source':{'type':'base64','media_type':'image/png','data':'AAAA'}}
    payload=[{'type':'text','text':'image-result'},image]
   else:
    payload=[{'type':'input_text','text':'image-result'},{'type':'input_image','image_url':'data:image/png;base64,AAAA'}]
   out=self.convert(protocol,['a','b'],[('b',payload),('a','plain')],True)
   tools=[m for m in out if m['role']=='tool']
   self.assertEqual(tools[0]['content'],'plain')
   self.assertIsInstance(tools[1]['content'],list)
   self.assertEqual(tools[1]['content'][0]['text'],'image-result')
   self.assertEqual(len(tools[1]['content']),2)
 def test_repeated_turns_reuse_ids(self):
  from serve.responses import input_messages
  for protocol in ('anthropic','responses'):
   if protocol=='anthropic':
    turns=[]
    for k in (1,2):
     turns += [{'role':'assistant','content':[{'type':'tool_use','id':c,'name':'read','input':{}} for c in ('a','b')]},
      {'role':'user','content':[{'type':'tool_result','tool_use_id':c,'content':str(k)+c} for c in ('b','a')]}]
    out=anthropic_to_messages({'messages':turns})[0]
   else:
    items=[]
    for k in (1,2):
     items += [{'type':'function_call','call_id':c,'name':'read','arguments':{}} for c in ('a','b')]
     items += [{'type':'function_call_output','call_id':c,'output':str(k)+c} for c in ('b','a')]
    out=input_messages({'input':items})
   self.assertEqual([m['content'] for m in out if m['role']=='tool'],['1a','1b','2a','2b'])
 def test_responses_custom_namespace(self):
  from serve.responses import input_messages
  out=input_messages({'input':[{'type':'custom_tool_call','call_id':c,'name':'exec','namespace':'shell','input':'echo '+c} for c in ('a','b')]+[{'type':'custom_tool_call_output','call_id':c,'output':c} for c in ('b','a')]})
  self.assertEqual([m['content'] for m in out if m['role']=='tool'],['a','b'])
  self.assertEqual(out[0]['tool_calls'][0]['function'],{'name':'shell.exec','arguments':{'input':'echo a'}})
