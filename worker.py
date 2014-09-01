import db
import bitsource

def add_message_to_db(message, block, txhash):
  dbstring="INSERT INTO MESSAGES (message, block, txhash) VALUES ("+str(message)+","+str(block)+","+str(txhash)+");"
  response=db.dbexecute(dbstring, True)
  return response

def block_opreturns_to_db(blockn):
  data=bitsource.opreturns_in_block_blockchain(blockn)

  for x in data:
    txhash=x[0]
    message=x[1]
    k=add_message_to_db(message, blockn, txhash)
    print k
  
