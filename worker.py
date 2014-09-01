import db
import bitsource

def parse(message):
  a=[]
  for x in message:
    if ord(x)<128:
      a.append(ord(x))
    else:
      a.append(63)
  c=""
  for b in a:
    c=c+chr(b)
  return c


def add_message_to_db(message, block, txhash):
  dbstring = "INSERT INTO MESSAGES (message, block, txhash) VALUES ('" +str(message)+"','"+str(block)+"','"+str(txhash)+"');"
  print dbstring
  response=db.dbexecute(dbstring, False)
  return response

def block_opreturns_to_db(blockn):
  data=bitsource.opreturns_in_block_blockchain(blockn)

  for x in data:
    txhash=str(x[0])
    message=parse(str(x[1]))
    print message
    k=add_message_to_db(message, str(blockn), txhash)
    print k
  db.dbexecute("UPDATE META SET lastblockdone='" + str(blockn)+"';",False)
