from itsdangerous import URLSafeSerializer
import uuid, M2Crypto
from scaffoldmaker_webapp import workspace
from scaffoldmaker_webapp import mesheroutput
import string
import random


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class MySession(object):

    def __init__(self):
        self.workspace = workspace.WorkspaceToLandmark()
        self.scaffold = mesheroutput.MyScaffold()

class MySessions(object):

    def __init__(self):
        self._sessions = {}
        self._s = URLSafeSerializer(M2Crypto.m2.rand_bytes(16))
        
    def getSession(self, encryted):
        try:
            id = self._s.loads(encryted)
            return self._sessions[id];
        except:
            return None
        
    def createNewSession(self):
        id = id_generator()
        newSession = MySession()
        self._sessions[id] = newSession
        encryted = self._s.dumps(id)
        return encryted , newSession
  