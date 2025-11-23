import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt

IMG_HT = 900
IMG_WIDTH = 900
BLACK_IMG = np.zeros((IMG_HT, IMG_WIDTH, 1), dtype='uint8') 
NUM_FRAMES = 450
SCALE = 2 # how scaled up the orbital window is compared to the transit one
BODIES = []
MOONS = []

DT = 1
STAR_RADIUS = 100

G = 1
M = 10000

K = (G * M) ** 0.5


def main(BODIES, MOONS):
    intensity_samples = []
    for _ in range(NUM_FRAMES):
        temp_img = BLACK_IMG.copy() # editing an image changes the original, so a copy is made first
        transiting_objects = []
        #go through every planet and move and draw them
        for body in BODIES:
            body.move()
            body.draw(temp_img) # every body will draw itself on canvas
            check = body.check()
            if check is not None:
                transiting_objects.append(check) # check if body is blocking star
        #repeat above loop but with the moons
        for body in MOONS:
            body.move()
            body.draw(temp_img)
            check = body.check()
            if check is not None:
                transiting_objects.append(check)
                
        draw_final_image(temp_img) # display final canvas
        intensity_samples.append(draw_transits(transiting_objects)) # measure avg intensity
        cv.moveWindow('Orbits', int(500-0.5*IMG_WIDTH), int(500-0.5*IMG_HT))  # Position of the first window (x, y)
        cv.moveWindow('Transits', int(500+0.5*IMG_WIDTH), int(500-0.5*IMG_HT))
        cv.setWindowProperty('Orbits', cv.WND_PROP_TOPMOST, 1)
        cv.setWindowProperty('Transits', cv.WND_PROP_TOPMOST, 1)
    
    relative_brightness = calc_rel_brightness(intensity_samples)
    plot_light_curve(relative_brightness) # plot brightness curve

    cv.destroyAllWindows()

def calc_rel_brightness(intensity_samples):
    """Return list of relative brightness from list of intensity values."""
    rel_brightness = []
    max_brightness = max(intensity_samples)
    for intensity in intensity_samples:
        rel_brightness.append(intensity / max_brightness)
    return rel_brightness

def plot_light_curve(rel_brightness):
    """Plot changes in relative brightness vs. time."""
    plt.plot(rel_brightness, color='red', linestyle='dashed',
    linewidth=2, label='Relative Brightness')
    plt.legend(loc='upper center')
    plt.title('Relative Brightness vs. Time')
    plt.show()

def draw_final_image(img):
    """Shows completed image after drawing the star"""
    cv.circle(img, (int(IMG_WIDTH/2), int(IMG_HT/2)), int(STAR_RADIUS), 255, -1)
    cv.imshow('Orbits', img)

def draw_transits(transiting_objects):
    """Draws a side-on view of the star and any planets block the light"""
    temp_img2 = BLACK_IMG.copy()
    cv.circle(temp_img2, (int(IMG_WIDTH/2), int(IMG_HT/2)), int(STAR_RADIUS*(SCALE)), 255, -1)
    for obj in transiting_objects:
        cv.circle(temp_img2, (int(obj.x), int(IMG_HT/2)), 
                  int(obj.RADIUS*SCALE), 0, -1)
    cv.imshow('Transits', temp_img2)
    cv.waitKey(DT*25)
    
    intensity = temp_img2.mean()
    return intensity
    
class Body():
    
    def __init__(self, apoapsis, radius, inclination = 0, periapsis = None, argument = np.pi*0.5):
        self.RADIUS = radius
        self.APO = apoapsis
        self.PERI = periapsis if periapsis is not None else apoapsis
        #self.INCLINATION = inclination*(np.pi/180)
        
        self.ECCENTRICITY = (self.APO - self.PERI)/(self.APO + self.PERI)
        self.ARGUMENT = argument
        
        self.angle = 0
        self.r = self.PERI
        self.K = (G * M) ** 0.5
        
        if type(self) == Body:
            BODIES.append(self)
        elif type(self) == Moon:        
            MOONS.append(self)
            self.K = (0.05*self.parent.RADIUS**3)**0.5


        
    def move(self): # geometrically calculate change in position
        self.angle -= DT * self.K / (self.r ** 1.5)
        self.r = ((self.APO + self.PERI)*(1 - self.ECCENTRICITY**2))/(1 + self.ECCENTRICITY * np.cos(self.angle + self.ARGUMENT))
    
    def draw(self, img): # draw planet on orbits image
        centre = (int(IMG_WIDTH/2 + self.r * np.sin(self.angle + self.ARGUMENT)), 
                  int(IMG_HT/2 + self.r * np.cos(self.angle + self.ARGUMENT)))
        cv.circle(img, centre, self.RADIUS, 150, -1)
        
    def check(self): # check if planet is in closer semicircle to observer
        y = self.r * np.cos(self.angle + self.ARGUMENT)
        if y > 0:
            self.x = int(IMG_WIDTH/2 + self.r * np.sin(self.angle + self.ARGUMENT) * SCALE)
            return self
        else:
            return None    


class Moon(Body):    
    def __init__(self, apoapsis, radius, parent):
        self.parent = parent
        super().__init__(apoapsis, radius, periapsis = apoapsis)

    def draw(self, img):
        parent_x = int(self.parent.r * np.sin(self.parent.angle + self.parent.ARGUMENT))
        parent_y = int(self.parent.r * np.cos(self.parent.angle + self.parent.ARGUMENT))

        centre = (int(IMG_WIDTH/2 + parent_x + self.r * np.sin(self.angle)),
                  int(IMG_HT/2 + parent_y + self.r * np.cos(self.angle)))
        cv.circle(img, centre, self.RADIUS, 100, -1)
        
    def check(self): # check if planet is in closer semicircle to observer
        parent_x = self.parent.r * np.sin(self.parent.angle + self.parent.ARGUMENT) * SCALE
        parent_y = self.parent.r * np.cos(self.parent.angle + self.parent.ARGUMENT)
        
        if parent_y > 0:
            self.x = IMG_WIDTH/2 + parent_x + self.r * np.sin(self.angle) * SCALE
            return self
        else:
            return None
        
#inclination given as degrees
#Body(apoapsis, radius)
a = Body(200, 15)
b = Body(120, 5)

c = Moon(25,1,a)
d = Moon(15,5,a)


if __name__ == '__main__':
    main(BODIES, MOONS) 
