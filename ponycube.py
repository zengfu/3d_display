# -*- coding: utf-8 -*-
# Rotate a cube with a quaternion
# Demo program
# Pat Hickey, 27 Dec 10
# This code is in the public domain.

import pygame
import pygame.draw
import pygame.time
import serial
import math
import struct
import time
from euclid import *


class Screen (object):
    def __init__(self,x=320,y=280,scale=1):
        self.i = pygame.display.set_mode((x,y))
        self.originx = self.i.get_width() / 2
        self.originy = self.i.get_height() / 2
        self.scale = scale

    def project(self,v):
        assert isinstance(v,Vector3)
        x = v.x * self.scale + self.originx
        y = v.y * self.scale + self.originy
        return (x,y)
    def depth(self,v):
        assert isinstance(v,Vector3)
        return v.z

class PrespectiveScreen(Screen):
    # the xy projection and depth functions are really an orthonormal space
    # but here i just approximated it with decimals to keep it quick n dirty
    def project(self,v):
        assert isinstance(v,Vector3)
        x = ((v.x*0.957) + (v.z*0.287)) * self.scale + self.originx
        y = ((v.y*0.957) + (v.z*0.287)) * self.scale + self.originy
        return (x,y)
    def depth(self,v):
        assert isinstance(v,Vector3)
        z = (v.z*0.9205) - (v.x*0.276) - (v.y*0.276)
        return z

class Side (object):
    def __init__(self,a,b,c,d,color=(50,0,0)):
        assert isinstance(a,Vector3)
        assert isinstance(b,Vector3)
        assert isinstance(c,Vector3)
        assert isinstance(d,Vector3)
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.color = color

    def centroid(self):
        return ( self.a + self.b + self.c + self.d ) / 4

    def draw(self,screen):
        assert isinstance(screen,Screen)
        s = [ screen.project(self.a)
            , screen.project(self.b)
            , screen.project(self.c)
            , screen.project(self.d)
            ]
        pygame.draw.polygon(screen.i,self.color,s)

    def erase(self,screen,clear_color = (0,0,0)):
        c = self.color
        self.color = clear_color
        self.draw(screen)
        self.color = c

class Edge (object):
    def __init__(self,a,b,color=(0,0,255)):
        assert isinstance(a,Vector3)
        assert isinstance(b,Vector3)
        self.a = a
        self.b = b
        self.color = color
    def centroid(self):
        return (self.a + self.b) / 2
    def draw(self,screen):
        assert isinstance(screen,Screen) 
        aa = screen.project(self.a)
        bb = screen.project(self.b)
        pygame.draw.line(screen.i, self.color, aa,bb)
    def erase(self,screen,clear_color = (0,0,0)):
        c = self.color
        self.color = clear_color
        self.draw(screen)
        self.color = c
        
        

class Cube (object):
    def __init__(self,a=10,b=10,c=10):
        self.a = a
        self.b = b
        self.c = c
        self.pts = [ Vector3(-a,b,c)  , Vector3(a,b,c)
                   , Vector3(a,-b,c)  , Vector3(-a,-b,c)
                   , Vector3(-a,b,-c) , Vector3(a,b,-c)
                   , Vector3(a,-b,-c) , Vector3(-a,-b,-c) ] 

    def origin(self):
        """ reset self.pts to the origin, so we can give them a new rotation """
        a = self.a; b = self.b; c = self.c
        self.pts = [ Vector3(-a,b,c)  , Vector3(a,b,c)
                   , Vector3(a,-b,c)  , Vector3(-a,-b,c)
                   , Vector3(-a,b,-c) , Vector3(a,b,-c)
                   , Vector3(a,-b,-c) , Vector3(-a,-b,-c) ] 

    def sides(self):
        """ each side is a Side object of a certain color """
        # leftright  = (80,80,150) # color
        # topbot     = (30,30,150)
        # frontback  = (0,0,150)
        one =   (255, 0, 0)
        two =   (0, 255, 0)
        three = (0, 0, 255)
        four =  (255, 255, 0)
        five =  (0, 255, 255)
        six =   (255, 0, 255)
        a, b, c, d, e, f, g, h = self.pts
        sides = [ Side( a, b, c, d, one)   #  front
                , Side( e, f, g, h, two)   #  back
                , Side( a, e, f, b, three) #  bottom
                , Side( b, f, g, c, four)  # right
                , Side( c, g, h, d, five)  # top
                , Side( d, h, e, a, six)   # left
                ]
        return sides

    def edges(self):
        """ each edge is drawn as well """
        ec         = (0,0,255) # color
        a, b, c, d, e, f, g, h = self.pts
        edges = [ Edge(a,b,ec), Edge(b,c,ec), Edge(c,d,ec), Edge(d,a,ec)
                , Edge(e,f,ec), Edge(f,g,ec), Edge(g,h,ec), Edge(h,e,ec)
                , Edge(a,e,ec), Edge(b,f,ec), Edge(c,g,ec), Edge(d,h,ec)
                ]
        return edges

    def erase(self,screen):
        """ erase object at present rotation (last one drawn to screen) """
        assert isinstance(screen,Screen)
        sides = self.sides()
        edges = self.edges()
        erasables = sides + edges
        [ s.erase(screen) for s in erasables]

    def draw(self,screen,q=Quaternion(1,0,0,0)):
        """ draw object at given rotation """
        assert isinstance(screen,Screen)
        self.origin()
        self.rotate(q)
        sides = self.sides()
        edges = self.edges()
        drawables = sides + edges
        drawables.sort(key=lambda s: screen.depth(s.centroid()))
        [ s.draw(screen) for s in drawables ]

    def rotate(self,q):
        assert isinstance(q,Quaternion)
        R = q.get_matrix()
        self.pts = [R*p for p in self.pts]

def eular2quat(roll,pitch,yaw):
    q1=math.cos(roll/2.)*math.cos(pitch/2.)*math.cos(yaw/2.)+math.sin(roll/2.)*math.sin(pitch/2.)*math.sin(yaw/2.)
    q2=math.sin(roll/2.)*math.cos(pitch/2.)*math.cos(yaw/2.)-math.cos(roll/2.)*math.sin(pitch/2.)*math.sin(yaw/2.)
    q3=math.cos(roll/2.)*math.sin(pitch/2.)*math.cos(yaw/2.)+math.sin(roll/2.)*math.cos(pitch/2.)*math.sin(yaw/2.)
    q4=math.cos(roll/2.)*math.cos(pitch/2.)*math.sin(yaw/2.)-math.sin(roll/2.)*math.sin(pitch/2.)*math.cos(yaw/2.)
    return Quaternion(q1,q2,q3,q4).normalized()



if __name__ == "__main__":
    pygame.init()
    pid=[0,0,0.1]
    font=pygame.font.SysFont("宋体", 30)
    t=serial.Serial('com4',115200)
    output = struct.pack('<3f', *pid)
    t.write(output)
    t.flushInput()
    screen =Screen(480,400,scale=1.5)
    cube = Cube(40,30,60)
    q = Quaternion(1,0,0,0)
    roll=0
    pitch=0
    yaw=0
    pos=0
    #incr = Quaternion(0.96,0.01,0.01,0).normalized()
    #incr = Quaternion(0,0.5,0.5,0).normalized()
    while 1:

        word = font.render(str(pid),True, (255, 0, 0))
        a=t.read(6)
        l=[]
        for i in range(6):
            l.append(ord(a[i]))
        rawroll=l[0:2]
        rawpitch=l[2:4]
        rawyaw=l[4:6]
        roll1=struct.pack('@2B',*rawroll)
        roll2=struct.unpack('>h',roll1)
        roll=int(list(roll2)[0])/10.0/57.3
        pitch1=struct.pack('@2B',*rawpitch)
        pitch2=struct.unpack('>h',pitch1)
        pitch=int(list(pitch2)[0])/10.0/57.3
        yaw1=struct.pack('@2B',*rawyaw)
        yaw2=struct.unpack('>h',yaw1)
        yaw=int(list(yaw2)[0])/10.0/57.3
        #print roll,pitch,yaw
        q = eular2quat(-roll,yaw,pitch)
        #q.normalize()
        cube.draw(screen,q)
        event = pygame.event.poll()
        if event.type == pygame.QUIT \
            or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            break
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_UP:
                pid[pos]=pid[pos]+0.1
                pid[pos]=round(pid[pos], 2)
            if event.key==pygame.K_LEFT:
                if pos!=0:
                    pos=pos-1
            if event.key == pygame.K_RIGHT:
                if pos!=2:
                    pos=pos+1
            if event.key == pygame.K_DOWN:
                pid[pos]=pid[pos]-0.1
                pid[pos]=round(pid[pos], 2)
        screen.i.blit(word, (000, 350))
        pygame.display.flip()
        pygame.time.delay(50)
        #time.sleep(1/50.0)
        cube.erase(screen)
        pygame.draw.rect(screen.i, (0, 0, 0), pygame.Rect((000, 350), (480, 40)))
        t.flushInput()

