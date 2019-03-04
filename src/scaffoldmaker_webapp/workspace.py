import os.path
import os
import traceback
import json
import code
import pdb
import tempfile

from requests import HTTPError
from requests import Session
from pmr2.wfctrl.core import get_cmd_by_name
from pmr2.wfctrl.core import CmdWorkspace
import pmr2.wfctrl.cmd
from urllib.parse import quote_plus
from requests_oauthlib.oauth1_session import TokenRequestDenied

try:
    import readline
except ImportError:
    pass

from pmr2.client import Client
from pmr2.client import DemoAuthClient

PMR2ROOT = 'http://models.physiomeproject.org'
CONSUMER_KEY = 'ovYoqjlJLrpCcEWcIFyxtqRS'
CONSUMER_SECRET = 'fHssEYMWZzgo6JWUBh4l1bhd'
DEFAULT_SCOPE = quote_plus(
    'http://models.physiomeproject.org/oauth_scope/collection,'
    'http://models.physiomeproject.org/oauth_scope/search,'
    'http://models.physiomeproject.org/oauth_scope/workspace_tempauth,'
    'http://models.physiomeproject.org/oauth_scope/workspace_full'
)

def createSuccessResponse(successMessage):
    return {'status':'success', 'message' : successMessage}

def createErrorResponse(errorMessage):
    return {'status':'error', 'message' : errorMessage}

class PMR2Workspace(object):
    
    def __init__(self):
        print(os.getcwd())
        self._currentDirectory = "tempdir/" + next(tempfile._get_candidate_names())
        self._git_implementation = 'git'
        
    def linkWorkspaceDirToUrl(self):
        # links a non-pmr workspace dir to a remote workspace url.
        # prereq is that the remote must be new.
        cmd_cls = get_cmd_by_name(self._git_implementation)
        if cmd_cls is None:
            print('Remote storage format unsupported')
        # brand new command module for init.
        new_cmd = cmd_cls()
        workspace = CmdWorkspace(self._currentDirectory, new_cmd)
        # Add the remote using a new command
        cmd = cmd_cls(remote=self._currentURL)
        # Do the writing.
        cmd.write_remote(workspace)
        
    def cloneWorkspace(self, credit):
        # XXX target_dir is assumed to exist, so we can't just clone
        # but we have to instantiate that as a new repo, define the
        # remote and pull.

        # link
        self.linkWorkspaceDirToUrl()

        workspace = CmdWorkspace(self._currentDirectory, get_cmd_by_name(self._git_implementation)())

        if credit:
            result = workspace.cmd.pull(workspace,
                username=credit['user'], password=credit['key'])
        else:
            # no credentials
            result = workspace.cmd.pull(workspace)
            
        print(self._currentDirectory)

        # TODO trap this result too?
        workspace.cmd.reset_to_remote(workspace)
        return result
        
    def commitFiles(self, message, files):
        workspace = CmdWorkspace(self._currentDirectory, get_cmd_by_name(self._git_implementation)())
        cmd = workspace.cmd

        for fn in files:
            sout, serr = cmd.add(workspace, fn)
            # if serr has something we need to handle?

        # XXX committer will be a problem if unset in git.
        return cmd.commit(workspace, message)

    def pushToRemote(self, credit, remote_workspace_url=None):
        workspace = CmdWorkspace(self._currentDirectory, get_cmd_by_name(self._git_implementation)())
        cmd = workspace.cmd

        if remote_workspace_url is None:
            remote_workspace_url = cmd.read_remote(workspace)

        stderr, stdout = cmd.push(workspace,
            username=credit['user'], password=credit['key'])

        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

        return stdout, stderr

    def pullFromRemote(self, credit):
        workspace = CmdWorkspace(self._currentDirectory, get_cmd_by_name(self._git_implementation)())
        cmd = workspace.cmd

        remote_workspace_url = cmd.read_remote(workspace)
        if credit:
            stdout, stderr = cmd.pull(workspace,
                username=credit['user'], password=credit['key'])
        else:
            stdout, stderr = cmd.pull(workspace)

        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

        return stdout, stderr
    
    def readFileContent(self, file):
        fullFileName = self._currentDirectory + "/" + file
        buffer = None
        with open(fullFileName, 'r') as myfile:
            buffer = myfile.read()
        return buffer
    
    def getContent(self, url, file, credit):
        self._currentURL = url
        if self._currentURL:
            print(self.cloneWorkspace(credit))
            buffer = self.readFileContent(file)
            d = json.loads(buffer)
            response = createSuccessResponse("Data successfully read")
            response["data"] = d
            return response
        
    def writeContent(self, file, content):
        fullFileName = self._currentDirectory + "/" + file
        with open(fullFileName, 'w') as myfile:
            myfile.write(content)
        
class PMR2Access(object):

    token_key = ''
    token_secret = ''
    active = False
    state = None
    _debug = 0
    last_response = None

    def __init__(self, 
            site=PMR2ROOT,
            consumer_key=CONSUMER_KEY, 
            consumer_secret=CONSUMER_SECRET,
            scope=DEFAULT_SCOPE,
        ):

        self.auth_client = DemoAuthClient(site, consumer_key, consumer_secret)
        self._currentURL = None
        self._awaitingVerifier = False
        self.client = None
        
        
    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        if isinstance(value, int):
            self._debug = value

        if isinstance(value, (str,bytes)):
            if value.lower() in ('false', 'no', '0',):
                self._debug = 0
            else:
                self._debug = 1
                
    def build_config(self):
        return  {
            'token_key':
                self.auth_client.session._client.client.resource_owner_key,
            'token_secret':
                self.auth_client.session._client.client.resource_owner_secret,
            'debug': self.debug,
            'scope': DEFAULT_SCOPE,
        }

    def load_config(self):
        config = self.build_config()
        token = config.get('token_key', '')
        secret = config.get('token_secret', '')
        self.auth_client.session._client.client.resource_owner_key = token
        self.auth_client.session._client.client.resource_owner_secret = secret
        self.debug = config.get('debug', 0)
        self.scope = config.get('scope', DEFAULT_SCOPE)
        return token and secret
    
    def _getObjectInfo(self, target_url):
        objectInfo = self.client(target=target_url)
        return objectInfo.response.json()

    def getObjectInfo(self, target_url):
        try:
            return self._getObjectInfo(target_url)
        except HTTPError as e:
            print('Remote server error')
        except JSONDecodeError:
            print('Unexpected Server Response')
        except Exception as e:
            print('Unexpected exception', str(e))
        
    def requestTemporaryPassword(self, workspace_url):
        credit = self.client(target=(
            '/'.join((workspace_url, 'request_temporary_password'))),
            data='{}'
        )
        return credit.response.json()
    
    def get_access(self):
        # get user to generate one.
        try:
            self.auth_client.fetch_request_token(scope=self.scope)
        except Exception as e:
            print('Fail to request temporary credentials.')
            return
        target = self.auth_client.authorization_url()
        return target
    
    def setVerifier(self, verifier):
        self.auth_client.set_verifier(verifier=verifier)
        token = self.auth_client.fetch_access_token()
        print(token)
        self._awaitingVerifier = False
        self.client = Client(PMR2ROOT,
            session=self.auth_client.session, use_default_headers=True)
        try:
            self.client()
        except ValueError as e:
            # JSON decoding error
            print('Credentials are invalid and are purged.  Quitting')
            self.auth_client.session._client.client.resource_owner_key = ''
            self.auth_client.session._client.client.resource_owner_secret = ''
            self.scope = DEFAULT_SCOPE
            self.save_config()
            return
        self.active = True
        
    def getAuthorizationURL(self):
        self.load_config()
        target = self.get_access()
        if target:
            self._awaitingVerifier = True
            response = createSuccessResponse("AuthorizationURL successfully called.")
            response['VerifyURL'] = target
            return response
        else:
            return createErrorResponse('Cannot get authorization url.')
        
    def tryURL(self, url):
        state = None
        if self.client:
            state = self.client(target = url)
        else:
            self.client = Client(use_default_headers=True)
            state = self.client(target = url)
        return state
        
    def getStateFromURL(self, workspaceURL):
        currentURL = workspaceURL 
        self._awaitingVerifier = False
        return self.tryURL(workspaceURL)

class WorkspaceToLandmark(object):
    
    def __init__(self):
        self.access = PMR2Access()
        self.workspace = PMR2Workspace()
        self._url= None
        self._filename = None
        
    def setVerifier(self, verifier):
        self.access.setVerifier(verifier)
        
    def getResponse(self, workspaceURL = None, filename = None):
        if workspaceURL != None:
            self._url = workspaceURL
        if filename != None:
            self._filename = filename
        if self._url and self._filename:
            state = self.access.getStateFromURL(self._url)
            if state.response.status_code == 200:
                if state._obj == None:
                    return self.access.getAuthorizationURL()
                else:
                    return self.workspace.getContent(self._url, self._filename, self.access.requestTemporaryPassword(self._url))
        return createErrorResponse('Invalid URL/filename.')
    
    def push(self):
        self.workspace.pushToRemote(self.access.requestTemporaryPassword(self._url))
        
    def writeToWorkspaceFile(self, string):
        self.workspace.writeContent(self._filename, string)
        
    def commit(self, message):
        response = self.workspace.commitFiles(message, [self._filename])
        print(response)
        if response[1]:
            return createErrorResponse('There is a problem with the commit.')
        else:
            return createSuccessResponse('Successfully committed changes.')
        
    def push(self):    
        response = self.workspace.pushToRemote(self.access.requestTemporaryPassword(self._url))
        print(response)
        if response[1]:
            return createErrorResponse('There is a problem with the push.')
        else:
            return createSuccessResponse('Successfully pushed the changes to repostory: ' + self._url)    
    