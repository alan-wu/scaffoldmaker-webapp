import logging
from json import loads, dumps
from time import time
from os.path import dirname
from os.path import join
from pkg_resources import get_distribution
from sanic import Sanic
from sanic.response import json, html, text, redirect
from scaffoldmaker_webapp import mesheroutput
from scaffoldmaker_webapp import backend
from scaffoldmaker_webapp import my_session

db_src = 'sqlite://'
app = Sanic()

with open(join(dirname(__file__), 'static', 'view.json')) as vd:
    view_json = loads(vd.read())
    
bundle_js = get_distribution('scaffoldmaker_webapp').get_metadata(
    'calmjs_artifacts/bundle.js')

store = backend.Store(db_src)
logger = logging.getLogger(__name__)

mySessions = my_session.MySessions()

def acquireSession(request):
    encryted = request.cookies.get('sessionid')
    mySession = None
    message = "Session resumed."
    if encryted:
        mySession = mySessions.getSession(encryted)
        if mySession == None:
            message = "Invalid session. New session has started."
            encryted, mySession = mySessions.createNewSession()
    else:
        message = "New session has started."
        encryted, mySession = mySessions.createNewSession()
    return encryted, mySession, message

def getMySession(request):
    mySession = mySessions.getSession(request.cookies.get('sessionid'))
    if mySession:
        return mySession
    else:
        raise Exception('Invalid session')
    

def build(mySession, typeName, options):
    print(mySession)
    model = mySession.scaffold.outputModel(typeName, options)
    job = backend.Job()
    job.timestamp = int(time())
    for data in model:
        resource = backend.Resource()
        resource.data = data
        job.resources.append(resource)
    response = loads(job.resources[0].data)
    store.add(job)
    for idx, obj in enumerate(response, 1):
        resource_id = job.resources[idx].id
        obj['URL'] = './output/%d' % resource_id
    return response
        
@app.route('/resume')
async def resume(request):
    encryted, mySession, message = acquireSession(request)
    if encryted and mySession:
        response = json({'message': message})
        settings = mySession.scaffold.getCurrentSettings()
        if settings:
            output = {}
            output['data'] = settings
            output['message'] = message
            response = json(output, dumps=dumps)
        response.cookies['sessionid'] = encryted
        response.cookies['sessionid']['httponly'] = True
        return response
    else:
        return json({'error': 'error starting/resuming session: ' + str(e)}, status=400)


@app.route('/output/<resource_id:int>')
async def output(request, resource_id):
    return json(store.query_resource(resource_id))

@app.route('/getPredefinedLandmarks')
async def getPredefinedLandmarks(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error getting predefined landmarks')
        return json({'error': 'error getting predefined landmarks: ' + str(e)}, status=400)
    annotations = mySession.scaffold.getPredefinedLandmarks()
    return json(annotations)

@app.route('/generator')
async def generator(request):
    mySession = None
    try:
        mySession = getMySession(request)
        print(mySession)
        print(mySession.scaffold)
    except Exception as e:
        logger.exception('error while generating mesh')
        return json({'error': 'error generating mesh: ' + str(e)}, status=400)  
    options = {}
    typeName = '3d_heartventricles1'
    for k, values in request.args.items():
        v = values[0]
        if k == 'meshtype':
            typeName = v
        elif k == 'Use cross derivatives':
            options[k] = v == 'true'
        elif v.isdecimal():
            options[k] = int(v)
        elif v.replace('.', '', 1).isdecimal():
            options[k] = float(v)
        elif v == 'false':
            options[k] = False
        elif v == 'true':
            options[k] = True

    if typeName not in mesheroutput.meshes.keys():
        return json({'error': 'no such mesh type'}, status=400)

    try:
        response = build(mySession, typeName, options)
    except Exception as e:
        logger.exception('error while generating mesh')
        return json({'error': 'error generating mesh: ' + str(e)}, status=400)

    return json(response)

@app.route('/getWorldCoordinates')
async def getWorldCoordinates(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while getting coordinates')
        return json({'error': 'error while getting coordinates: ' + str(e)}, status=400)  
    xiCoordinates = [0.0, 0.0, 0.0]
    elementId = 1
    for k, values in request.args.items():
        v = values[0]
        if k == 'element':
            elementId = int(v)
        elif k == 'xi1':
            xiCoordinates[0] = float(v)
        elif k == 'xi2':
            xiCoordinates[1] = float(v)
        elif k == 'xi3':
            xiCoordinates[2] = float(v)
    coordinates = mySession.scaffold.getWorldCoordinates(elementId, xiCoordinates)
    return json(coordinates)

@app.route('/getXiCoordinates')
async def getXiCoordinates(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while getting coordinates')
        return json({'error': 'error while getting coordinates: ' + str(e)}, status=400)  
    coordinates = [0.0, 0.0, 0.0]
    for k, values in request.args.items():
        v = values[0]
        if k == 'xi1':
            coordinates[0] = float(v)
        elif k == 'xi2':
            coordinates[1] = float(v)
        elif k == 'xi3':
            coordinates[2] = float(v)
    xiCoordinates = mySession.scaffold.getXiCoordinates(coordinates)
    return json(xiCoordinates)

@app.route('/registerLandmarks')
async def registerLandmarks(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while registering landmark')
        return json({'error': 'error while registering landmark: ' + str(e)}, status=400)  
    coordinates = [0.0, 0.0, 0.0]
    name = 'temp'
    for k, values in request.args.items():
        v = values[0]
        if k == 'xi1':
            coordinates[0] = float(v)
        elif k == 'xi2':
            coordinates[1] = float(v)
        elif k == 'xi3':
            coordinates[2] = float(v)
        elif k == 'name':
            name = v
    xiCoordinates = mySession.scaffold.registerLandmarks(name, coordinates)
    return json(xiCoordinates)
                
@app.route('/getMeshTypes')
async def getMeshTypes(request):
    return json(sorted(mesheroutput.meshes.keys()))

@app.route('/getCurrentSettings')
async def getCurrentSettings(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while retrieving settings')
        return json({'error': 'error while retrieving settings: ' + str(e)}, status=400)
    settings = mySession.scaffold.getCurrentSettings()
    if settings is None:
        return json({'error': 'no such mesh type'}, status=400)
    return json(settings, dumps=dumps)

@app.route('/checkMeshTypeOptions')
async def checkMeshTypeOptions(request):
    options = {}
    typeName = '3d_heartventricles1'
    for k, values in request.args.items():
        v = values[0]
        if k == 'meshtype':
            typeName = v
        elif k == 'Use cross derivatives':
            options[k] = v == 'true'
        elif v.isdecimal():
            options[k] = int(v)
        elif v.replace('.', '', 1).isdecimal():
            options[k] = float(v)
        elif v == 'false':
            options[k] = False
        elif v == 'true':
            options[k] = True
    options = mesheroutput.checkMeshTypeOptions(typeName, options)
    if options is None:
        return json({'error': 'no such mesh type'}, status=400)
    return json(options, dumps=dumps)

@app.route('/getMeshTypeOptions')
async def getMeshTypeOptions(request):
    options = mesheroutput.getMeshTypeOptions(request.args.get('type'))
    if options is None:
        return json({'error': 'no such mesh type'}, status=400)
    return json(options, dumps=dumps)

@app.route('/getWorkspaceResponse')
async def getWorkspaceResponse(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while getting response from workspace')
        return json({'error': 'error while getting response from workspace: ' + str(e)}, status=400)
    url = ""
    filename = ""
    for k, values in request.args.items():
        v = values[0]
        if k == 'url':
            url = v
        elif k == 'filename':
            filename = v
    print(url, filename)
    response = mySession.workspace.getResponse(url, filename)
    return json(response)

@app.route('/verifyAndResponse')
async def verifyAndResponse(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while verifying your workspace')
        return json({'error': 'error while verifying your workspace: ' + str(e)}, status=400)
    verifier = ""
    for k, values in request.args.items():
        v = values[0]
        if k == 'v':
            verifier = v
    mySession.workspace.setVerifier(v)
    response = mySession.workspace.getResponse()
    return json(response)

@app.route('/commitWorkspaceChanges')
async def commitWorkspaceChanges(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while committing changes')
        return json({'error': 'error while committing changes: ' + str(e)}, status=400)
    message = ""
    for k, values in request.args.items():
        v = values[0]
        if k == 'msg':
            message = v
    settings = mySession.scaffold.getCurrentSettings()
    if settings is None:
        return json({'status':'error', 'message': 'Settings unavailable'}, status=400)
    buffer = dumps(settings)
    mySession.workspace.writeToWorkspaceFile(buffer)
    response = mySession.workspace.commit(message)
    return json(response)

@app.route('/pushWorkspace')
async def pushWorkspace(request):
    mySession = None
    try:
        mySession = getMySession(request)
    except Exception as e:
        logger.exception('error while pushing changes')
        return json({'error': 'error while pushing changes: ' + str(e)}, status=400)
    response = mySession.workspace.push()
    return json(response)

@app.route('/scaffoldmaker_webapp.js')
async def serve_js(request):
    return text(bundle_js, headers={'Content-Type': 'application/javascript'})

@app.route('/static/view.json')
async def view(request):
    return json(view_json)

html_file = join(dirname(__file__), 'static', 'scaffold.html')
app.static('/scaffold.html', html_file)

js_file = join(dirname(__file__), 'static', 'physiomeportal.js')
app.static('/physiomeportal.js', js_file)



def main():
    app.run(host='0.0.0.0', port=6565)


if __name__ == '__main__':
    main()
