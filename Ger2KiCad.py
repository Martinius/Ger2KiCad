#################################Ger2KiCad####################################
#This script allows to transform gerber files into kicad_mod files           #
##############################################################################
#Author:                                           E-Mail:                   #
#Martin Obermaier                                  Martin.Obermaier@posteo.de#
##############################################################################


##############################################################################
#                                  Imports                                   #
##############################################################################
import gerber
import re
import numpy as np
##############################################################################
 #                              Define Classes                               #
##############################################################################

class Polygon:

    def __init__(self):
        self.vertices = []
    
    def add_vertex(self,x,y):
        self.vertices.append([x,y])
        
    def get_vertices(self):
        return self.vertices
        
    def remove_vertex(self,x,y):
        self.vertices.remove([x,y])
    

##############################################################################
#                          Variables and Constants                           #
##############################################################################


# Regex Filters:

MODE = r"(Mode):\s([a-z]{1,})"
SCALE = r"(Scale) Factor:\sX:\s(\d+\.\d+|\d+)\sY:\s(\d+\.\d+|\d+)"
COOR = r"(Coordinate Statement):\s([X,Y]):\s(-?\d+\.\d+|-?\d+)\s(?:(Y):\s"+\
        "(-?\d+\.\d+|-?\d+))?.{1,}Lights\s(On|Off)"
RMStmtStart = r"(RegionModeStmt) type=RegionMode units=(metric|inch) mode=(on)"
RMStmtStop = r"(RegionModeStmt) type=RegionMode units=(metric|inch) mode=(off)"
EOF = r"EOF Statement"


Scale = [0.0,0.0]
offset = [0.0, 0.0]

mm = 1.0
inch = 25.4

mode = ""

##############################################################################
#                              Functions                                     #
##############################################################################


def setMode(Stmt):
    global mode 
    mode = re.search(MODE,Stmt).group(2)
    print(Stmt)
    
def setScale(Stmt):
    global Scale 
    Scale[0] = np.float(re.search(SCALE,Stmt).group(2));
    Scale[1] = np.float(re.search(SCALE,Stmt).group(3));
    print(Stmt)
    print(Scale)
    
def new_Polygon(Stmts):
    LastStmt = 0;
    unit = ""
    poly = Polygon()
    LastCoor = [0.0,0.0]
    #print(Stmts)
    for cnt in range(len(Stmts)):
        res = re.search(RMStmtStart,Stmts[cnt])
        if res != None:
            unit = res.group(2)
            LastStmt = cnt+1
            break
    
    if unit == "metric":
        factor = mm
    else:
        factor = inch
    
    for cnt in range(LastStmt,len(Stmts)):
        coor = [] 
        res = re.search(COOR,Stmts[cnt])
        if res.group(6) == "Off":
            x = np.float(res.group(3))*factor
            y = np.float(res.group(5))*factor
            coor = [x,y]
        elif res.group(6) =="On":
            if res.group(2) != None and res.group(4) != None:
                x = np.float(res.group(3))*factor
                y = np.float(res.group(5))*factor
            else:
                if res.group(2) == "X":
                 x = np.float(res.group(3))*factor
                 y = LastCoor[1]
                else:
                 y = np.float(res.group(3))*factor
                 x = LastCoor[0]
            coor = [x,y]
        coor = np.round(coor,4)
        poly.add_vertex(coor[0],coor[1])
        LastCoor = coor  

    return poly

def find_center(polygons):
    xmax = np.array([], dtype=np.float64)
    xmin = np.array([], dtype=np.float64)

    ymax = np.array([], dtype=np.float64)
    ymin = np.array([], dtype=np.float64)

    for pol in polygons:
        poly_coor = np.asarray(pol.get_vertices())
        
        xmax = np.append(xmax,np.amax(poly_coor[::,0]))
        xmin = np.append(xmin,np.amin(poly_coor[::,0]))
        
        ymax = np.append(ymax,np.amax(poly_coor[::,1]))
        ymin = np.append(ymin,np.amin(poly_coor[::,1]))




    x_c = (np.amax(xmax)+np.amin(xmin))/2
    y_c = (np.amax(ymax)+np.amin(ymin))/2
    return x_c,y_c

def readGerber(file):
    top_copper = gerber.read(file).statements
    polygons =[]
    LastStmtIndex = 0;

    #Find mode statement
    for cnt in range(len(top_copper)):
     Stmt = str(top_copper[cnt])
     if re.search(MODE,Stmt) != None:
        setMode(Stmt)
        LaststmtIndex = cnt;
        break
        

    if mode == "":
        raise Exception("FileFormat","No Unit mode Statement found")

    #Find scale factors  
    for cnt in range(LastStmtIndex,len(top_copper)):
     Stmt = str(top_copper[cnt])
     if re.search(SCALE,Stmt) != None:
        setScale(Stmt)
        LaststmtIndex = cnt;
        break

    #Find polygons factors


    for cnt in range(LastStmtIndex,len(top_copper)):
     Stmt = str(top_copper[cnt])
     if re.search(RMStmtStart ,Stmt) != None:
        PolyStmt = []    
        i = 0
        while cnt+i < len(top_copper):
            Stmt = str(top_copper[cnt+i])
            if re.search(RMStmtStop ,Stmt) != None:
                LaststmtIndex = cnt+i;  
                poly = new_Polygon(PolyStmt)
                polygons.append(poly)
                break 
            else:
                PolyStmt.append(Stmt)
                i+=1   
    
    return polygons
    
def create_kicad_poly(polygons,x_c,y_c,layer="F.Cu"):

    polygon_str = ""
    for pol in polygons:

        poly_frame ="  (fp_poly (pts"
        poly_end =") (layer "+ layer +") (width 0.001))"

        new_poly = poly_frame

        flat_list = pol.get_vertices()
        for cnt in range(len(flat_list)):
	        cor = flat_list[cnt]
	        cor_x = np.round(float(cor[0])-x_c,4)
	        cor_y = np.round(float(cor[1])-y_c,4)
	        a="(xy "+str(cor_x)+" "+str(cor_y)+")"
	        new_poly+=" "+a
	        
        new_poly_com=new_poly+poly_end
        polygon_str += new_poly_com + "\n"
    return polygon_str
    

def create_kicad_mod(name,polygons,libary="Default",tedit="5EF5C08B"):

    kicad_file = ""

    header = "(module "+libary+":"+name+" (layer F.Cu) (tedit "+tedit+\
             ")"+"\n"+ \
             "(fp_text reference REF** (at 0.0 5.0) (layer F.SilkS) hide"+\
             "\n"+ \
             "(effects (font (size 1 1) (thickness 0.15)))"+"\n"+ \
             ")"+"\n"+ \
             "(fp_text value "+name+" (at 0.0 -5.0) (layer F.Fab) hide"+\
             "\n"+ \
             "(effects (font (size 1 1) (thickness 0.15)))"+"\n"+\
             ")"+"\n"
             
    footer = ")"
    kicad_file += header;
    for poly in polygons:
        kicad_file += poly
    
    kicad_file += footer
        
    return kicad_file
    

##############################################################################
#                                   Main                                     #
##############################################################################




poly=readGerber('BP.ger')
x_c,y_c = find_center(poly)
kicad_poly = create_kicad_poly(poly,x_c,y_c,layer="F.Cu")
output=create_kicad_mod("BP",kicad_poly)

f= open("BP.kicad_mod","w+")
f.write(output)
f.close()


exit();
##############################################################################
#                                   END                                      #
##############################################################################



