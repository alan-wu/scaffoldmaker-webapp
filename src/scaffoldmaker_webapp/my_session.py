from itsdangerous import URLSafeSerializer
import uuid, M2Crypto
from scaffoldmaker_webapp import workspace
from scaffoldmaker_webapp import mesheroutput
import string
import random
import threading

def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class MySession(object):

    def __init__(self, owner, id):
        self.duration = 86400.0 # 24 hours
        self.owner = owner
        self.id = id
        self.workspace = workspace.WorkspaceToLandmark()
        self.scaffold = mesheroutput.MyScaffold()
        self.timer = threading.Timer(self.duration, self.expire)
        self.timer.start()
    
    def __del__(self):
        print("Session expired, deleting")
        del self.workspace
        del self.scaffold
        
    def expire(self):
        self.timer = None
        self.owner.removeSessionById(self.id)
        
    def renew(self):
        self.timer.cancel()
        self.timer = threading.Timer(self.duration, self.expire)
        self.timer.start()
        return True

class MySessions(object):

    def __init__(self):
        self._sessions = {}
        self._s = URLSafeSerializer(M2Crypto.m2.rand_bytes(16))
        
    def removeSessionById(self, id):
        try:
            session = self._sessions[id]
            del self._sessions[id]
            del session
        except KeyError:
            print('Key not found')
        
    def getSession(self, encryted):
        try:
            id = self._s.loads(encryted)
            session = self._sessions[id]
            session.renew()
            return session
        except:
            return None
        
    def createNewSession(self):
        id = id_generator()
        newSession = MySession(self, id)
        self._sessions[id] = newSession
        encryted = self._s.dumps(id)
        return encryted , newSession
  