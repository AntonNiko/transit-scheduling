from itertools import permutations
import csv

PROJECT_ROOT_DATA_DIR = "data/"
STOPS_FILE = "stops.csv"

class Node():
    node_id = None
    node_name = None
    node_stops = []
    connections = []
    
    def __init__(self, node_id, node_name, node_stops):
        self.node_id = node_id
        self.node_name = node_name
        self.node_stops = node_stops
        
        self.generateConnections()

    def generateConnections(self):
        ## Method which generates a connection between every stops in the node
        self.connections = list(permutations(self.node_stops, 2))

    def evaluateConnectionTime(self, trips):
        print("Evaluating Node: {} --- {}".format(self.node_id, self.node_name))
        for connection in self.connections:
            print(connection)
        
            
          
        
        
        
        
        
                    
            
            
        
