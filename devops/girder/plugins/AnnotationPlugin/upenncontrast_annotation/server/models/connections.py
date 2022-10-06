from girder.models.model_base import AccessControlledModel
from girder.exceptions import GirderException, ValidationException
from girder.constants import AccessType
from girder import events
from girder.utility import optionalArgumentDecorator

from bson.objectid import ObjectId
from bson.errors import InvalidId
from girder.models.folder import Folder

from .annotation import Annotation
from ..helpers.connections import annotationToAnnotationDistance

import jsonschema
import numpy as np

@optionalArgumentDecorator
def cacheDB(fun, maxSize = 100):
  cached = dict()
  def inner(*args, **kwargs):
    cacheSize = len(cached)
    if cacheSize == maxSize:
      cached.clear()
    channelId = kwargs['channelId']
    location = kwargs['location']
    tags = kwargs['tags']
    key = (channelId, tuple(tags), (location['XY'], location['Z'], location['Time']))
    if key not in cached:
      cached[key] = fun(*args,**kwargs)
      cacheSize +=  1
    return cached[key]
  return inner

class ConnectionSchema:
    tagsSchema = {
        'type': 'array',
        'items': {
            'type': 'string'
        }
    }

    connectionSchema = {
        '$schema': 'http://json-schema.org/schema#',
        'id': '/girder/plugins/upenncontrast_annotation/models/annotation_connection',
        'type': 'object',
        'properties': {
            'label': {'type': 'string'},
            'parentId': {'type': 'string'},
            'childId': {'type': 'string'},
            'datasetId': {'type': 'string'},
            'tags': tagsSchema
        },
        'required': ['parentId', 'childId', 'datasetId', 'tags']
    }

class AnnotationConnection(AccessControlledModel):
  # TODO: write lock
  # TODO(performance): indexing

  validator = jsonschema.Draft4Validator(
        ConnectionSchema.connectionSchema
    )

  def cleanOrphanedAnnotation(self, event):
    if event.info and event.info['_id']:
      annotationId = str(event.info['_id'])
      query = {
        '$or': [
          {
            'childId': annotationId
          },
          {
            'parentId': annotationId
          }
        ]
      }
      self.removeWithQuery(query)

  def cleanOrphanedDataset(self, event):
    if event.info and event.info['_id']:
      folderId = str(event.info['_id'])
      query = {
        "datasetId": folderId,
      }
      self.removeWithQuery(query)

  def initialize(self):
    self.name="annotation_connection"
    events.bind('model.upenn_annotation.remove', 'upenn.connections.clean.orphans.annotation', self.cleanOrphanedAnnotation)
    events.bind('model.folder.remove', 'upenn.connections.clean.orphans.dataset', self.cleanOrphanedDataset)

  def validate(self, document):
    try:
      self.validator.validate(document)
    except jsonschema.ValidationError as exp:
        raise ValidationException(exp)

    folder = Folder().load(document['datasetId'], force=True)
    if folder is None:
      raise ValidationException('Dataset does not exist')
    if 'meta' not in folder or folder['meta'].get('subtype', None) != 'contrastDataset':
      raise ValidationException('Folder is not a dataset')

    child = Annotation().load(document['childId'], force=True)
    if child is None:
      raise ValidationException('Child does not exist')

    parent = Annotation().load(document['parentId'], force=True)
    if parent is None:
      raise ValidationException('Parent does not exist')

    return document

  def create(self, creator, connection):
    self.setUserAccess(connection, user=creator, level=AccessType.ADMIN, save=False)
    return self.save(connection)

  def delete(self, connection):
    self.remove(self.find(connection))

  def update(self, connection):
    return self.save(connection)
  
  def getClosestAnnotation(self, annotationRef, annotations):
    """Get the closest annotation based on its distance to a reference annotation.

    Args:
        annotationRef (any): the annotation of reference
        annotations (any): a list of annotations

    Returns:
        Tuple(Annotation, Number): Returns a tuple of 2 items: the closest annotation and the minimum distance
    """
    
    annotations2 = [annotation for annotation in annotations if annotation["_id"] != annotationRef["_id"]]
    distances = np.array([(annotation, annotationToAnnotationDistance(annotationRef, annotation)) for annotation in annotations2])
    sortDistances = np.argsort(distances[:, 1])
    return distances[sortDistances[0], :]
  
  @cacheDB(maxSize=50)
  def getAnnotations(self, channelId = None, tags = None, location = None):
    query = {}
    if channelId is not None and isinstance(channelId, int) :
      query.update({"channel": channelId})
    if tags is not None and len(tags) > 0:
      query.update({"tags": {  "$in": tags }})
    if location is not None: 
      query.update({"location": location})
    
    return list(Annotation().find(query))

  def connectToNearest(self, info, user=None):
    # annotation ids, a list of tags and a channel index.
    connections = []

    annotationsIdsToConnect = info['annotationsIds']
    if not annotationsIdsToConnect or len(annotationsIdsToConnect) == 0:
      raise GirderException('Missing annotations ids: ', annotationsIdsToConnect)
    
    ids = None
    try:
      ids = [ObjectId(id) for id in annotationsIdsToConnect]
    except InvalidId:
      raise ValidationException('Invalid ObjectId format. Should be a list of strings and not ObjectIds.', id)

    # query = {}
    # channelId can be None if not specify
    channelId = int(info.get("channelId", None)) if info.get("channelId", None) is not None else None
    tags = info.get("tags", [])

    # Loop on each annotation to connect
    # Look for the closest annotation and connect to it
    for id in ids:
      annotation = Annotation().getAnnotationById(id, user)

      if annotation is None:
        print("Annotation not defined", id)
        continue
      # Compute distance
      closestAnnotation = None

      # Only work on annotations that are placed in the same tile
      location = annotation["location"]
      
      annotations = self.getAnnotations(channelId=channelId, tags=tags, location=location)

      # Find the closest annotation
      (closestAnnotation, _) = self.getClosestAnnotation(annotation, annotations)
      
      # Define connection
      if closestAnnotation is not None:
        connections.append(self.create(creator=user, connection={
          "tags": [],
          "label": "A Connection",
          "parentId": str(closestAnnotation['_id']),
          "childId": str(id),
          "datasetId": annotation["datasetId"]
        }))

    return connections
