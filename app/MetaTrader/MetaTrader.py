from .MetaTrader import MetaTrader
from loguru import logger
import MetaTrader5 as mt5

class MetaTrader:
  def __init__(self, server, user, password):
    self.server = server
    self.user = user
    self.password = password
    
  @logger.catch
  def Login(server, user, password):
    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize(login=user, server=server,password=password):
        print("initialize() failed, error code =",mt5.last_error())
        quit()