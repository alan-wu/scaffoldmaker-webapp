"""
Generates 3-D Left and Right ventricles mesh starting from modified sphere shell mesh.
"""

import os
import json
import math
import collections
from scaffoldmaker.scaffolds import Scaffolds
from opencmiss.zinc.context import Context
from opencmiss.zinc.material import Material

meshes = {
    meshtype.__name__[len('MeshType_'):]: meshtype
    for meshtype in Scaffolds().getMeshTypes()
}

def getMeshTypeOptions(meshtype):
    """
    Provided meshtype must exist as a key in the meshes dict in this
    module, otherwise return value will be None.
    """
    meshtype_cls = meshes.get(meshtype)
    if not meshtype_cls:
        return None
    defaultOptions = meshtype_cls.getDefaultOptions()
    orderedNames = meshtype_cls.getOrderedOptionNames()
    orderedOptions=collections.OrderedDict()
    orderedOptions.update(defaultOptions)
    for option in orderedNames:
        orderedOptions.update({option:defaultOptions[option]})
    return orderedOptions

def checkMeshTypeOptions(meshtype, options):
    """
    Provided meshtype must exist as a key in the meshes dict in this
    module, otherwise return value will be None.
    """
    meshtype_cls = meshes.get(meshtype)
    if not meshtype_cls:
        return None
    defaultOptions = meshtype_cls.getDefaultOptions()
    defaultOptions.update(options)
    changed = meshtype_cls.checkOptions(defaultOptions)
    orderedNames = meshtype_cls.getOrderedOptionNames()
    orderedOptions=collections.OrderedDict()
    for option in orderedNames:
        orderedOptions.update({option:defaultOptions[option]})
    return orderedOptions

class MyScaffold(object):

    def __init__(self):
        self._currentRegion = None
        self._currentOptions = None
        self._currentMeshType = None
        self._currentLandmarks = []
    
    def createCylindeLineGraphics(self, context, region):
        '''create cylinders which outline the shapes of the heart'''
        scene = region.getScene()
        field_module = region.getFieldmodule()
        material_module = context.getMaterialmodule()
        material = material_module.findMaterialByName('silver')
    
        scene.beginChange()
        lines = scene.createGraphicsLines()
        finite_element_field = field_module.findFieldByName('coordinates')
        lines.setCoordinateField(finite_element_field)
        lineAttr = lines.getGraphicslineattributes()
        lineAttr.setShapeType(lineAttr.SHAPE_TYPE_CIRCLE_EXTRUSION)
        lineAttr.setBaseSize([0.01, 0.01])
        lines.setMaterial(material)
        lines.setExterior(True)
         # Let the scene render the scene.
        scene.endChange()
    
    def createSurfaceGraphics(self, context, region, annotationGroups):
        material_module = context.getMaterialmodule()
        scene = region.getScene()
        scene.beginChange()
        fieldmodule = region.getFieldmodule()
        material_module.defineStandardMaterials()
        material = material_module.findMaterialByName('muscle')
        material.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [0.7, 0.12, 0.1])
        material.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [0.7, 0.14, 0.11])
        finite_element_field = fieldmodule.findFieldByName('coordinates')
        for annotationGroup in annotationGroups:
            groupField = annotationGroup.getGroup()
            surface = scene.createGraphicsSurfaces()
            tessellation = surface.getTessellation()
            tessellation.setRefinementFactors([4])
            if groupField:
                surface.setSubgroupField(groupField)
            surface.setCoordinateField(finite_element_field)
            surface.setExterior(True)        
            surface.setMaterial(material)
        scene.endChange()
    
    
    def exportWebGLJson(self, region):
        '''
        Export graphics into JSON format, one json export represents one
        surface graphics.
        '''
        scene = region.getScene()
        sceneSR = scene.createStreaminformationScene()
        sceneSR.setIOFormat(sceneSR.IO_FORMAT_THREEJS)
    
        # Get the total number of graphics in a scene/region that can be exported
        number = sceneSR.getNumberOfResourcesRequired()
        resources = []
        # Write out each graphics into a json file which can be rendered with our
        # WebGL script
        for i in range(number):
            resources.append(sceneSR.createStreamresourceMemory())
        scene.write(sceneSR)
        # Write out each resource into their own file
    
        return [resources[i].getBuffer()[1] for i in range(number)]
    
    
    def finaliseOptions(self, meshtype_cls, provided_options):
        options = {}
        default_options = meshtype_cls.getDefaultOptions()
        for key, default_value in default_options.items():
            provided_value = provided_options.get(key)
            if type(default_value) != type(provided_value):
                # TODO figure out how to propagate type mistmatch issue to
                # response.
                options[key] = default_value
            else:
                options[key] = provided_value
        return options
    
    def getWorldCoordinates(self, elementId, xiCoordinates):
        fieldmodule = self._currentRegion.getFieldmodule()
        mesh = fieldmodule.findMeshByDimension(3)
        element = mesh.findElementByIdentifier(elementId)
        finite_element_field = fieldmodule.findFieldByName('coordinates')
        cache = fieldmodule.createFieldcache()
        cache.setMeshLocation(element, xiCoordinates)
        result = finite_element_field.evaluateReal(cache, 3)
        outputs = {}
        outputs["coordinates"] = result[1]
        print(outputs)
        return outputs
    
    
    def getXiCoordinates(self, coordiantes):
        print(coordiantes)
        fieldmodule = self._currentRegion.getFieldmodule()
        mesh = fieldmodule.findMeshByDimension(3)
        finite_element_field = fieldmodule.findFieldByName('coordinates')
        meshLocationField = fieldmodule.createFieldFindMeshLocation(finite_element_field, finite_element_field, mesh)
        cache = fieldmodule.createFieldcache()
        cache.setFieldReal(finite_element_field, coordiantes)
        result = meshLocationField.evaluateMeshLocation(cache, 3)
        outputs = {}
        outputs["element"] = result[0].getIdentifier()
        outputs["xi"] = result[1]
        print(outputs)
        return outputs
        
    
    def registerLandmarks(self, name, coordinates):
        outputs = self.getXiCoordinates(coordinates)
        landmark = {}
        landmark['name'] = name
        landmark['xi'] = outputs["xi"]
        landmark['element'] = outputs["element"]
        self._currentLandmarks.append(landmark)
        return outputs
    
    def meshGeneration(self, meshtype_cls, region, options):
        self._currentLandmarks = []
        fieldmodule = region.getFieldmodule()
        fieldmodule.beginChange()
        myOptions = self.finaliseOptions(meshtype_cls, options)
        self._currentOptions = myOptions
        groups = meshtype_cls.generateMesh(region, myOptions)
        fieldmodule.defineAllFaces()
        fieldmodule.endChange()
        for annotationGroup in groups:
            annotationGroup.addSubelements()
        return groups
    
    def getPredefinedLandmarks(self):
        if self._currentRegion:
            annotations = []
            fm = self._currentRegion.getFieldmodule()
            datapoints = fm.findNodesetByName("datapoints")
            iter = datapoints.createNodeiterator()
            data = iter.next()
            while data.isValid():
                finite_element_field = fm.findFieldByName('data_coordinates')
                label_field = fm.findFieldByName('data_label')
                cache = fm.createFieldcache()
                cache.setNode(data)
                retCoordinates = finite_element_field.evaluateReal(cache, 3)
                retLabel = label_field.evaluateString(cache)
                if retCoordinates[0] and retLabel:
                    annotation = {}
                    annotation['name'] = retLabel
                    annotation['coordinates'] = retCoordinates[1]
                    annotations.append(annotation)
                data = iter.next()
        return annotations
    
    def outputModel(self, meshtype, options):
        """
        Provided meshtype must exist as a key in the meshes dict in this
        module.
        """
        print(self._currentRegion)
        # Initialise a sceneviewer for viewing
        meshtype_cls = meshes.get(meshtype)
        defaultOptions = meshtype_cls.getDefaultOptions()
        self._currentMeshType = meshtype
        context = Context('output')
        logger = context.getLogger()
        context.getGlyphmodule().defineStandardGlyphs()
        region = context.createRegion()
        self._currentRegion = region
        print(self._currentRegion)
        defaultOptions.update(options)
        #readTestRegion(region)
        annotations = self.meshGeneration(meshtype_cls, region, defaultOptions)
        # Create surface graphics which will be viewed and exported
        tm = context.getTessellationmodule()
        tessellation = tm.getDefaultTessellation()
        tessellation.setCircleDivisions(6)
        tessellation.setMinimumDivisions(1)
    
        self.createSurfaceGraphics(context, region, annotations)
        self.createCylindeLineGraphics(context, region)
        # Export graphics into JSON format
        return self.exportWebGLJson(region)
    
    def getCurrentSettings(self):
        if self._currentMeshType and self._currentOptions:
            meshtype_cls = meshes.get(self._currentMeshType)
            if not meshtype_cls:
                return None
            outputArray = {}
            orderedNames = meshtype_cls.getOrderedOptionNames()
            orderedOptions=collections.OrderedDict()
            for option in orderedNames:
                orderedOptions.update({option:self._currentOptions[option]})
            outputArray["options"]  = orderedOptions
            outputArray["meshtype"] = self._currentMeshType
            outputArray["landmarks"] = self._currentLandmarks
            return outputArray
        return None
    
