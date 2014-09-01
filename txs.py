import addresses
from bitcoin import *
import node

profit_address="1C3nG7RpEGq5VzVWdygM4RY35qJji8fx2c"
dust=5461*0.00000001
max_op_length=37


def make_raw_one_input(fromaddress,amount,destination,fee, specific_inputs):  #NEEDS REWORKING
  global ins, outs, totalin
  fee=int(fee*100000000)
  amount=int(amount*100000000)
  #unspents=unspent(fromaddress)
  #unspents=[unspents[input_n]]
  unspents=specific_inputs

  ins=[]
  outs=[]
  totalin=0

  print 'unspents below'
  print unspents
  print ''

  for uns in unspents:
    if 'value' in uns:
      totalin=totalin+uns['value']
      ins.append(uns)

  if totalin>=amount+fee:
    outs.append({'value': amount, 'address': destination})
  extra=totalin-amount-fee
  if extra>=dust*100000000:
    outs.append({'value':extra, 'address':fromaddress})


  tx=mktx(ins,outs)
  return tx

def make_raw(fromaddress,destination,fee):  #TAILORED FOR THIS SPECIFIC USE CASE
  global ins, outs, totalin
  fee=int(fee*100000000)
  unspents=addresses.unspent(fromaddress)

  ins=[]
  outs=[]
  totalin=0

  print 'unspents below'
  print unspents
  print ''

  for uns in unspents:
    if 'value' in uns:
      totalin=totalin+uns['value']
      ins.append(uns)

  if totalin>=fee+int(dust*100000000):
    outs.append({'value': totalin-fee, 'address': destination})

  tx=mktx(ins,outs)
  return tx


def make_op_return_script(message):
   #OP RETURN SCRIPT
   hex_message=message.encode('hex')
   hex_message_length=hex(len(message))

   r=2
   f=''
   while r<len(hex_message_length):
      f=f+hex_message_length[r]
      r=r+1
   if len(f)<2:
      f='0'+f

   b='6a'+f+hex_message
   return b

def add_op_return(unsigned_raw_tx, message, position_n):
  deserialized_tx=deserialize(unsigned_raw_tx)

  newscript=make_op_return_script(message)

  newoutput={}
  newoutput['value']=0
  newoutput['script']=newscript

  if position_n>=len(deserialized_tx['outs']):
    deserialized_tx['outs'].append(newoutput)
  else:
    deserialized_tx['outs'].insert(position_n,newoutput)
  #deserialized_tx['outs'].append(newoutput)

  reserialized_tx=serialize(deserialized_tx)

  return reserialized_tx

def sign_tx(unsigned_raw_tx, privatekey):
  tx2=unsigned_raw_tx

  detx=deserialize(tx2)
  input_length=len(detx['ins'])

  for i in range(0,input_length):
    tx2=sign(tx2,i,privatekey)

  return tx2

def pushtx(rawtx):
  print "Trying to push: "+ str(rawtx)
  response=node.connect('sendrawtransaction',[rawtx])
  print "Push Response was "+str(response)

  return response

def send_op_return(fromaddr, dest, fee, message, privatekey, specific_inputs):
  #specific_input=cointools.unspent(fromaddr)
  #specific_input=specific_input[specific_input_n]

  #tx=make_raw_one_input(fromaddr,dust,dest,fee, specific_input)

  amt=dust
  tx=make_raw_one_input(fromaddr, amt, dest, fee, specific_inputs)

  tx2=add_op_return(tx,message,1)
  tx3=sign_tx(tx2,privatekey)
  print tx3
  response=pushtx(tx3)
  #response=''
  #print "Trying to push op return: "
  print tx3
  print "Response: "+str(response)
  return response


def make_raw_multiple_outputs(fromaddress, output_n, output_amount_each, destination, fee):

  global ins, outs,h, tx, tx2, outputs
  outputs=[]
  for i in range(0,output_n):
    outputs.append({'value': int(output_amount_each*100000000), 'address': destination})

  fee=int(fee*100000000)

  unspents=addresses.unspent(fromaddress)  #using vitalik's version could be problematic

  totalout=0
  for x in outputs:
    totalout=totalout+x['value']
  ins=[]
  ok=False
  outs=[]
  totalfound=0
  for unsp in unspents:
    ins.append(unsp)
    totalfound=totalfound+unsp['value']
  change_amount=totalfound-totalout-fee
  outs=outputs
  if change_amount>int(dust*100000000):
    outs.append({'value': change_amount, 'address': profit_address})

  print 'ins'
  print ins
  print ''
  print 'outs'
  print outs

  tx=mktx(ins,outs)

  return tx

def make_multiple_outputs(fromaddress, privatekey, output_n, value_each,  total_fee):  #WORKS
  tx=make_raw_multiple_outputs(fromaddress, output_n, value_each, fromaddress, total_fee)
  tx2=sign_tx(tx, privatekey)
  response=pushtx(tx2)
  free_outputs=[]
  for i in range(0,output_n):
    outputdata={}
    outputdata['output']=str(response)+":"+str(i)
    outputdata['value']= int(value_each*100000000)
    free_outputs.append(outputdata)
  print ''
  print free_outputs
  return free_outputs


def declaration_tx(fromaddr, fee_each, privatekey, message):
  global specific_inputs
  n_transactions=len(message)/max_op_length+1
  continu=True
  responses=[]
  #PREPARE OUTPUTS
  value_each=fee_each
  specific_inputs=make_multiple_outputs(fromaddr, privatekey, n_transactions+1, value_each, fee_each)

  for n in range(0,n_transactions):
    if continu:
      indexstart=max_op_length*n
      indexend=indexstart+max_op_length
      if indexend>len(message):
        indexend=len(message)
      specific_input=specific_inputs[n:n+1]
      print ""
      print "MY INPUT: "+str(specific_input)
      print ""
      submessage=str(n)+" "+message[indexstart:indexend]
      #print submessage
      r=send_op_return(fromaddr, profit_address, fee_each, submessage, privatekey,specific_input)

      if r is None:
        continu=False
      else:
        responses.append(r)
  return specific_inputs


m='Celebrimbor was the son of Curufin, fifth son of F\xc3\xabanor and Nerdanel.'
declaration_tx(addresses.generate_publicaddress('Andrew1Barisser'), 0.00004, addresses.generate_privatekey('Andrew1Barisser'),m)
