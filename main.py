import math
import os
import random
import time
from copy import deepcopy

from PIL import Image

from painting import Painting


# Calculate histogram difference between two images
def score(x: Painting) -> float:
    current_score = x.image_diff(x.target_image)
    # print(".", end='', flush=True)
    return current_score


# Pick one best chromosome and randomize the other
def pick_best_and_random(pop, maximize=False):
    evaluated_individuals = tuple(filter(lambda x: x.fitness is not None, pop))
    if len(evaluated_individuals) > 0:
        mom = max(evaluated_individuals, key=lambda x: x.fitness if maximize else -x.fitness)
    else:
        mom = random.choice(pop)
    dad = random.choice(pop)
    return mom, dad


# Mutate a chromosome based on parameters
def mutate_painting(x: Painting, rate=0.04, swap=0.5, sigma=1) -> Painting:
    x.mutate_triangles(rate=rate, swap=swap, sigma=sigma)
    return deepcopy(x)


# Return an offspring if given two parents
def mate(mom: Painting, dad: Painting):
    child_a, child_b = Painting.mate(mom, dad)

    return deepcopy(child_a)


# A container for a Painting, this associate a painting with a fitness score.
class Chromosome:
    def __init__(self, painting: Painting):
        self.painting = painting
        self.fitness = score(self.painting)

    def set_fitness(self, fitness):
        self.fitness = fitness

    def get_score(self):
        return self.fitness

    def calculate_fitness(self):
        self.fitness = score(self.painting)


# A container for Chromosome, it's just a fancy List with special methods/functions
class Population:
    def __init__(self, generator, sample_size, generation_count=0, maximize=False):
        print("Creating population...")
        start_time = time.time()
        self.pop = []
        self.sample_size = sample_size
        self.generation_count = generation_count
        self.maximize = maximize
        self.generator = generator
        self.current_best = Chromosome(generator)
        self.previous_best = Chromosome(generator)
        self.pop.append(self.current_best)
        self.pop.append(self.previous_best)
        self.gain = 0.0
        self.rememberer = 0

        # Create random solutions
        for _ in range(abs(self.sample_size - len(self.pop))):
            self.pop.append(Chromosome(generator))

        self.avg_fitness = sum(i.fitness for i in self.pop) / float(len(self.pop))
        print(f"Population with {self.sample_size} members created in {(time.time() - start_time):.2f} seconds")

    # Calculate the difference between the fitness score of 2 chromosomes
    def get_gain(self):
        pb = self.previous_best.get_score()
        cb = self.current_best.get_score()
        gain = abs(pb - cb)
        return gain

    # A function to stop the program when there is no improvement after a set generation.
    def progress_bouncer(self, threshold=5):
        if self.gain == 0:
            self.rememberer += 1
        else:
            self.rememberer = 0

        if self.rememberer == threshold:
            raise Exception(f"No Gain found in the last {self.rememberer} generation")

    # Survive: Eliminate a percentage of the population based on their fitness score
    def eliminate(self, survival_rate: float = 0.025):
        survived_individuals = math.floor(self.sample_size * survival_rate)
        try:
            self.pop.sort(key=lambda x: x.fitness)
            self.previous_best = self.current_best
            self.current_best = self.pop[0]
            self.gain = self.get_gain()
            self.pop = self.pop[:survived_individuals]
        except AttributeError:
            print(f"len(self.pop) = {len(self.pop)}")

    # Breed: Use the remaining population to repopulate
    def breed(self, select_method, mate_method, mutate_method, rate, swap, sigma):
        try:
            temp = []
            while len(temp) < self.sample_size - len(self.pop):
                mom, dad = select_method(self.pop)
                painting = mate_method(mom.painting, dad.painting)
                painting = mutate_method(painting, rate, swap, sigma)
                temp.append(Chromosome(painting))
            self.pop.extend(temp)

            not_0 = abs(self.sample_size - len(self.pop))
            if not_0 != 0:
                raise ValueError

        except ValueError:
            print(f"There is {not_0} chromosome missing")

        self.generation_count += 1

    # Repeat: Fancy for loop, evolve the generation for "n" generation.
    def evolve(self, generation, survival_rate, selection_method, mating_method, mutate_method, rate, swap, sigma):
        # print("Evolving population...")
        for _ in range(generation):
            start_time = time.time()
            self.eliminate(survival_rate)
            self.breed(selection_method, mating_method, mutate_method,
                       rate=rate, swap=swap, sigma=sigma)
            self.print_summary()
            self.progress_bouncer(180)
            print(f"Evolved in {(time.time() - start_time):,.2f} seconds.")

    def print_summary(self):
        # checkpoint_path = "/home/erklarungsnot/PycharmProjects/ai_ga_art_ass2/output/"
        checkpoint_path = "./output2/"
        image_template = os.path.join(checkpoint_path, "drawing_%05d.png")

        # if self.generation_count % 50 == 0:
        print(
            f"\nCurrent generation {self.generation_count},"
            f" best score {self.current_best.get_score():,.2f},"
            f" gain {self.gain:,.2f}")
        if self.gain != 0:
            img = self.current_best.painting.draw(scale=1)
            img.save(image_template % self.generation_count, 'PNG')


if __name__ == "__main__":
    # Program settings
    target_image_path = "./image/lamp.png"
    # target_image_path = "./image/girl.png"
    # target_image_path = "./image/v.gordeev.png"
    # target_image_path = "./image/head.jpg"
    target_image = Image.open(target_image_path).convert('RGBA')

    # Population settings
    num_triangles = 250
    population_size = 100

    # Genetic Settings (getting triangles to the optimal position)
    e_step = 200
    s_rate = 0.60
    # s_rate = 0.35
    r_rate = 0.20
    sw_rate = 0.75
    sigma = 1

    # Creating initial population rgb(37, 150, 190)
    pop = Population(Painting(num_triangles, target_image, background_color=(0, 0, 1)), population_size)

    # 200 generations
    pop.evolve(generation=e_step, survival_rate=s_rate, selection_method=pick_best_and_random, mating_method=mate,
               mutate_method=mutate_painting, rate=r_rate,
               swap=sw_rate, sigma=sigma)

    # Genetic Setting 2
    e_step = 300
    r_rate = 0.15
    sw_rate = 0.5
    sigma = 1

    # 200 generations
    pop.evolve(generation=e_step, survival_rate=s_rate, selection_method=pick_best_and_random, mating_method=mate,
               mutate_method=mutate_painting,
               rate=r_rate,
               swap=sw_rate, sigma=sigma)

    # Genetic Setting 3 (Slowdown the rate moving rate, resizing the triangles)
    # e_step = 1000
    e_step = 300
    r_rate = 0.05
    sw_rate = 0.25

    # 200 generations
    pop.evolve(generation=e_step, survival_rate=s_rate, selection_method=pick_best_and_random, mating_method=mate,
               mutate_method=mutate_painting, rate=r_rate,
               swap=sw_rate, sigma=sigma)

    # Genetic Setting 4
    # e_step = 1500
    e_step = 300
    r_rate = 0.05
    sw_rate = 0
    sigma = 0.5

    # 200 generations
    pop.evolve(generation=e_step, survival_rate=s_rate, selection_method=pick_best_and_random, mating_method=mate,
               mutate_method=mutate_painting, rate=r_rate,
               swap=sw_rate, sigma=sigma)

    # Genetic Setting 5 (Color optimization)
    # e_step = 2000
    e_step = 300
    r_rate = 0.03
    sw_rate = 0
    sigma = 0.12

    # 300 generations
    pop.evolve(generation=e_step, survival_rate=s_rate, selection_method=pick_best_and_random, mating_method=mate,
               mutate_method=mutate_painting, rate=r_rate,
               swap=sw_rate, sigma=sigma)
