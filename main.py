"""Mochi's Dream Garden — original cozy adventure, Python 3.10 + pygame."""
import json, math, random, sys
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent
SAVE = ROOT / 'savegame.json'
W,H = 1100,700
WORLD_W,WORLD_H = 2040,1320
FPS=60
PINK=(255,183,205); LAV=(198,175,237); INK=(83,72,107); CREAM=(255,250,240)
random.seed(24)
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("Mochi's Dream Garden ✿")
clock=pygame.time.Clock()
FONTS={size:pygame.font.SysFont('segoeui',size,bold=bold) for size,bold in [(15,False),(18,False),(21,False),(24,True),(28,True),(34,True),(48,True),(62,True)]}
SOUNDS={}
for name in ('collect','plant','quest','step','ui'):
    try: SOUNDS[name]=pygame.mixer.Sound(str(ROOT/'assets'/(name+'.wav')))
    except (pygame.error,FileNotFoundError): pass

def sound(name):
    if name in SOUNDS: SOUNDS[name].play()
def font(size=21,bold=False):
    return FONTS.get((size,bold),FONTS[(21,False)])
def txt(s,x,y,size=21,color=INK,center=False,bold=False):
    surf=font(size,bold).render(str(s),True,color)
    screen.blit(surf,(x-surf.get_width()//2 if center else x,y))
def rr(rect,color,r=18,border=None,bw=2):
    pygame.draw.rect(screen,color,rect,border_radius=r)
    if border: pygame.draw.rect(screen,border,rect,bw,border_radius=r)
def circle(x,y,r,color): pygame.draw.circle(screen,color,(int(x),int(y)),int(r))
def heart(x,y,s=12,col=(255,126,158)):
    circle(x-s*.4,y-s*.15,s*.55,col);circle(x+s*.4,y-s*.15,s*.55,col)
    pygame.draw.polygon(screen,col,[(x-s,y),(x+s,y),(x,y+s)])
def star(x,y,r=11,col=(255,225,119),rot=0):
    pts=[]
    for i in range(10):
        angle=rot-math.pi/2+i*math.pi/5
        radius=r if i%2==0 else r*.48
        pts.append((x+math.cos(angle)*radius,y+math.sin(angle)*radius))
    pygame.draw.polygon(screen,col,pts)
def flower(x,y,scale=1,color=(250,157,189),bloom=True):
    pygame.draw.line(screen,(110,167,125),(x,y+14*scale),(x,y-4*scale),max(2,int(3*scale)))
    if bloom:
        for k in range(5):
            ang=k*math.tau/5
            circle(x+math.cos(ang)*7*scale,y-6*scale+math.sin(ang)*7*scale,5.8*scale,color)
        circle(x,y-6*scale,5*scale,(255,229,127))
    else:
        circle(x,y-4*scale,6*scale,(125,190,132))
def bunny(x,y,t=0,scale=1):
    bob=math.sin(t*6)*2*scale
    x=int(x);y=int(y+bob)
    circle(x,y+19*scale,16*scale,(205,184,211))
    pygame.draw.ellipse(screen,(252,248,250),(x-18*scale,y-6*scale,36*scale,39*scale))
    for d in (-1,1):
        pygame.draw.ellipse(screen,(252,248,250),(x+(d*10-7)*scale,y-40*scale,14*scale,34*scale))
        pygame.draw.ellipse(screen,(251,190,207),(x+(d*10-3)*scale,y-33*scale,6*scale,22*scale))
    circle(x-7*scale,y+8*scale,2.8*scale,INK);circle(x+7*scale,y+8*scale,2.8*scale,INK)
    circle(x-12*scale,y+13*scale,4*scale,(255,194,204));circle(x+12*scale,y+13*scale,4*scale,(255,194,204))
    circle(x,y+15*scale,2.5*scale,(221,125,155))
    pygame.draw.arc(screen,(245,178,200),(x-12*scale,y-4*scale,24*scale,10*scale),0,math.pi,2)
def friend(x,y,kind,t):
    bob=math.sin(t*2+x)*2
    colors={'Pip':(251,201,139),'Lulu':(190,221,187),'Boba':(206,189,226)}
    col=colors[kind];circle(x,y+14+bob,23,col)
    if kind=='Pip':
        pygame.draw.polygon(screen,col,[(x-18,y),(x-17,y-25),(x-3,y-9)])
        pygame.draw.polygon(screen,col,[(x+18,y),(x+17,y-25),(x+3,y-9)])
    elif kind=='Lulu':
        circle(x-13,y-9+bob,10,col);circle(x+13,y-9+bob,10,col)
    else:
        circle(x-16,y-5+bob,9,col);circle(x+16,y-5+bob,9,col)
    circle(x-8,y+12+bob,3,INK);circle(x+8,y+12+bob,3,INK)
    circle(x-13,y+19+bob,5,(255,174,187));circle(x+13,y+19+bob,5,(255,174,187))
    circle(x,y+20+bob,2,(158,115,142))

# Deterministic handcrafted meadow, no external image downloads required.
DECOR=[]
for i in range(260):
    x=random.randrange(40,WORLD_W-40);y=random.randrange(70,WORLD_H-50)
    kind=random.choice(('petal','petal','flower','mushroom','bush','sparkle'))
    DECOR.append((x,y,kind,random.randrange(4)))
PONDS=[(300,990,140,75),(1670,350,175,90)]
FRIENDS=[('Pip',390,320),('Lulu',1630,860),('Boba',1040,1080)]
STAR_POS=[(230,460),(580,250),(810,620),(1150,240),(1410,480),(1820,600),(420,1080),(920,920),(1320,1050),(1840,1100),(730,1140),(1710,160)]
PATCHES=[(540,490),(680,490),(820,490),(960,490),(1100,490),(1240,490),(610,740),(760,740),(910,740),(1060,740),(1210,740),(1360,740)]

class Game:
    def __init__(self):
        self.x,self.y=1020.,650.;self.stars=0;self.planted=[];self.collected=[];self.done=[];self.t=0
        self.scene='menu';self.notice='';self.notice_until=0;self.show_journal=False;self.speed=225;self.spark=[]
        self.load()
    def load(self):
        if not SAVE.exists():return
        try:
            d=json.loads(SAVE.read_text(encoding='utf-8'))
            self.x=float(d.get('x',1020));self.y=float(d.get('y',650));self.stars=int(d.get('stars',0))
            self.planted=[int(i) for i in d.get('planted',[]) if int(i) in range(len(PATCHES))]
            self.collected=[int(i) for i in d.get('collected',[]) if int(i) in range(len(STAR_POS))]
            self.done=[i for i in d.get('done',[]) if i in ('Pip','Lulu','Boba')]
        except (ValueError,KeyError,TypeError,OSError): pass
    def save(self):
        d={'x':round(self.x,1),'y':round(self.y,1),'stars':self.stars,'planted':self.planted,'collected':self.collected,'done':self.done}
        try: SAVE.write_text(json.dumps(d,indent=2),encoding='utf-8')
        except OSError:self.say('Could not save progress')
    def say(self,s):self.notice=s;self.notice_until=self.t+4
    def particles(self,x,y,col,count=14):
        for _ in range(count):
            ang=random.random()*math.tau;vel=random.randrange(40,145)
            self.spark.append([x,y,math.cos(ang)*vel,math.sin(ang)*vel,random.uniform(.5,1.1),col])
    def nearest(self):
        candidates=[]
        for i,(x,y) in enumerate(STAR_POS):
            if i not in self.collected:candidates.append((math.hypot(self.x-x,self.y-y),('star',i)))
        for i,(x,y) in enumerate(PATCHES):
            if i not in self.planted:candidates.append((math.hypot(self.x-x,self.y-y),('patch',i)))
        for name,x,y in FRIENDS:candidates.append((math.hypot(self.x-x,self.y-y),('friend',name)))
        return min(candidates,key=lambda c:c[0]) if candidates else (999,None)
    def interact(self):
        dist,target=self.nearest()
        if dist>90 or target is None:
            self.say('Move closer to a star, flower bed, or friend!');return
        kind,idx=target
        if kind=='star':
            self.collected.append(idx);self.stars+=2;sound('collect');self.say('+2 stardust! So sparkly!')
            self.particles(*STAR_POS[idx],(255,222,123));self.save()
        elif kind=='patch':
            if self.stars<2:self.say('You need 2 stardust to plant a dream flower!');return
            self.stars-=2;self.planted.append(idx);sound('plant');self.say('A dream flower bloomed!')
            self.particles(*PATCHES[idx],PINK);self.save()
        else:
            name=idx
            if name in self.done:self.say({'Pip':'Pip: Your garden is magical!','Lulu':'Lulu: Ribbit! Thank you, Mochi!','Boba':'Boba: Best garden party ever!'}[name]);sound('ui');return
            need={'Pip':3,'Lulu':6,'Boba':10}[name]
            if len(self.planted)>=need:
                self.done.append(name);self.stars+=4;sound('quest');self.say(f'{name} is delighted! Quest complete: +4 stardust!')
                self.particles(*next((x,y) for n,x,y in FRIENDS if n==name),(255,228,125),30);self.save()
            else:
                self.say(f'{name}: Plant {need} dream flowers! ({len(self.planted)}/{need})');sound('ui')
    def update(self,dt,keys):
        self.t+=dt
        if self.scene!='play' or self.show_journal:return
        dx=(keys[pygame.K_d] or keys[pygame.K_RIGHT])-(keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy=(keys[pygame.K_s] or keys[pygame.K_DOWN])-(keys[pygame.K_w] or keys[pygame.K_UP])
        if dx or dy:
            mag=math.hypot(dx,dy);self.x=max(35,min(WORLD_W-35,self.x+dx/mag*self.speed*dt));self.y=max(75,min(WORLD_H-35,self.y+dy/mag*self.speed*dt))
        for p in self.spark[:]:
            p[0]+=p[2]*dt;p[1]+=p[3]*dt;p[4]-=dt
            if p[4]<=0:self.spark.remove(p)
    def camera(self):return max(0,min(WORLD_W-W,self.x-W/2)),max(0,min(WORLD_H-H,self.y-H/2))
    def background(self,cx,cy):
        screen.fill((205,234,216))
        for x in range(-80,W+100,80):
            for y in range(-80,H+100,80):
                wx=int((x+cx)//80);wy=int((y+cy)//80)
                if (wx*7+wy*11)%5==0:circle(x-cx%80+20,y-cy%80+28,2,(188,224,197))
        # central meandering stone path
        points=[(120,630),(370,600),(640,620),(940,620),(1220,610),(1490,660),(1920,690)]
        pp=[(int(x-cx),int(y-cy)) for x,y in points]
        pygame.draw.lines(screen,(245,226,204),False,pp,98)
        pygame.draw.lines(screen,(255,243,223),False,pp,79)
        for px,py,rx,ry in PONDS:
            rect=pygame.Rect(px-rx-cx,py-ry-cy,rx*2,ry*2)
            pygame.draw.ellipse(screen,(172,216,207),rect.inflate(22,20))
            pygame.draw.ellipse(screen,(158,208,218),rect)
            pygame.draw.ellipse(screen,(197,235,236),rect.inflate(-35,-35),3)
        for x,y,kind,v in DECOR:
            sx=x-cx;sy=y-cy
            if sx<-35 or sx>W+35 or sy<-35 or sy>H+35:continue
            if kind=='petal':circle(sx,sy,3,((255,240,240),(249,220,237),(248,246,202),(226,212,244))[v])
            elif kind=='flower':flower(sx,sy,.65,((255,163,188),(240,194,243),(255,211,145),(248,241,250))[v])
            elif kind=='bush':
                for dx,dy in ((-12,4),(0,-4),(12,4)):circle(sx+dx,sy+dy,12,(147,197,155))
                circle(sx+3,sy-8,3,PINK)
            elif kind=='mushroom':
                rr(pygame.Rect(sx-3,sy,6,12),(251,239,222),2)
                pygame.draw.ellipse(screen,((255,179,197),(209,180,237))[v%2],(sx-11,sy-8,22,13))
                circle(sx-4,sy-4,2,CREAM)
            else:star(sx,sy,4,(253,248,209),self.t*.4)
        for i,(x,y) in enumerate(PATCHES):
            sx=x-cx;sy=y-cy
            if -50<sx<W+50 and -50<sy<H+50:
                pygame.draw.ellipse(screen,(192,169,151),(sx-26,sy-12,52,28))
                pygame.draw.ellipse(screen,(213,191,172),(sx-22,sy-10,44,21))
                if i in self.planted:flower(sx,sy,1.55,((255,158,186),(209,164,245),(255,213,143))[i%3])
                else:circle(sx,sy,3,(150,124,113))
        for i,(x,y) in enumerate(STAR_POS):
            if i in self.collected:continue
            sx=x-cx;sy=y-cy
            if -40<sx<W+40 and -40<sy<H+40:
                circle(sx,sy+math.sin(self.t*3+i)*5,19,(240,240,201))
                star(sx,sy+math.sin(self.t*3+i)*5,13,(255,209,102),self.t*.3)
        for name,x,y in FRIENDS:
            sx=x-cx;sy=y-cy
            friend(int(sx),int(sy),name,self.t)
            rr(pygame.Rect(sx-35,sy-62,70,22),CREAM,10)
            txt(name,sx,sy-60,15,INK,True)
            if name in self.done:heart(sx+35,sy-48,7)
        bunny(self.x-cx,self.y-cy,self.t,1.15)
        for x,y,vx,vy,life,col in self.spark:circle(x-cx,y-cy,max(1,life*5),col)
    def ui(self):
        rr(pygame.Rect(18,16,345,86),(255,250,245),22,(240,219,227))
        txt('MOCHI\'S DREAM GARDEN',35,27,24,INK,bold=True)
        star(48,78,11);txt(f'{self.stars} stardust',65,65,21)
        flower(225,78,.7);txt(f'{len(self.planted)}/12 flowers',241,65,18)
        rr(pygame.Rect(W-245,16,226,86),(255,250,245),22,(240,219,227))
        txt('GARDEN JOURNEY',W-225,27,18,INK)
        txt(f'{len(self.done)}/3 friend quests',W-225,61,21,INK)
        rr(pygame.Rect(18,H-60,680,43),(255,250,245),16)
        txt('WASD / Arrows  Move    E  Interact    J  Journal    P  Pause    Esc  Menu',32,H-48,15)
        dist,target=self.nearest()
        if dist<90 and target:
            kind,idx=target
            desc={'star':'Collect stardust','patch':'Plant flower (2 stars)','friend':'Talk to '+str(idx)}[kind]
            rr(pygame.Rect(W//2-135,H-117,270,44),CREAM,16,(231,199,214))
            txt('E  '+desc,W//2,H-106,18,INK,True)
        if self.notice and self.t<self.notice_until:
            rect=pygame.Rect(W//2-265,117,530,49);rr(rect,(255,247,229),19,(248,213,173))
            txt(self.notice,W//2,129,18,INK,True)
    def journal(self):
        veil=pygame.Surface((W,H),pygame.SRCALPHA);veil.fill((72,60,93,140));screen.blit(veil,(0,0))
        rr(pygame.Rect(230,100,640,505),CREAM,28,(242,193,215),4)
        txt('✿  Mochi\'s Little Journal  ✿',W//2,135,34,INK,True,True)
        txt('Help your friends by growing dream flowers!',W//2,195,21,INK,True)
        for i,(name,_,_) in enumerate(FRIENDS):
            needed={'Pip':3,'Lulu':6,'Boba':10}[name]
            y=250+i*86
            rr(pygame.Rect(285,y,530,69),(248,233,238),17)
            txt(('♥ ' if name in self.done else '☆ ')+name,309,y+12,24,INK,bold=True)
            txt('Complete!' if name in self.done else f'Grow {needed} flowers  •  {len(self.planted)}/{needed}',470,y+16,18)
        txt('Press J or Esc to return to your garden',W//2,551,18,INK,True)
    def overlay(self,paused=False):
        veil=pygame.Surface((W,H),pygame.SRCALPHA);veil.fill((97,78,112,105));screen.blit(veil,(0,0))
        rr(pygame.Rect(245,130,610,420),CREAM,35,(244,192,216),5)
        for i in range(15):
            x=275+(i*101)%540;y=155+(i*73)%345
            star(x,y,6,((255,216,135),(231,197,246))[i%2],self.t*.3)
        bunny(W//2,277,self.t,2)
        txt('PAUSED' if paused else "Mochi's Dream Garden",W//2,375,48,INK,True,True)
        txt('A tiny adventure, full of big little wonders',W//2,433,21,INK,True)
        rr(pygame.Rect(350,481,400,45),PINK,20)
        txt('Press ENTER to continue' if paused else 'Press ENTER to begin',W//2,491,21,INK,True)
    def draw(self):
        cx,cy=self.camera();self.background(cx,cy);self.ui()
        if self.show_journal:self.journal()
        if self.scene in ('menu','pause'):self.overlay(self.scene=='pause')

def main():
    game=Game();autosave=0
    while True:
        dt=min(clock.tick(FPS)/1000,.04)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:game.save();pygame.quit();return
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_RETURN and game.scene in ('menu','pause'):
                    game.scene='play';sound('ui')
                elif event.key==pygame.K_ESCAPE:
                    if game.show_journal:game.show_journal=False
                    elif game.scene=='play':game.scene='menu';game.save()
                    elif game.scene=='pause':game.scene='play'
                elif event.key==pygame.K_p and game.scene in ('play','pause'):
                    game.scene='pause' if game.scene=='play' else 'play'
                elif event.key==pygame.K_j and game.scene=='play':game.show_journal=not game.show_journal;sound('ui')
                elif event.key==pygame.K_e and game.scene=='play' and not game.show_journal:game.interact()
        game.update(dt,pygame.key.get_pressed());game.draw();pygame.display.flip()
        autosave+=dt
        if autosave>25:game.save();autosave=0
if __name__=='__main__':main()
