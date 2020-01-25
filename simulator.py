#!/usr/bin/env python3

import requests
import threading
import random
import time
from enum import Enum
import argparse
import signal


BASE_URL = "https://api.clmb.live"
DELAY_MULTIPLIER = 100.0
PLEASE_EXIT = False


def signal_handler(sig, frame):
    global PLEASE_EXIT
    print('Shutting down...')
    PLEASE_EXIT = True


def main():
    global DELAY_MULTIPLIER

    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--delay", type=int, default=100, help="delay multiplier")
    parser.add_argument("input", default="contenders.txt", help="contenders file")
    args = parser.parse_args()

    DELAY_MULTIPLIER = float(args.delay)

    registration_codes = []
    with open(args.input, "r") as f:
        for line in f.readlines():
            registration_codes.append(line.strip())

    print("Loaded registration codes for %d contenders" % (len(registration_codes)))
    print("Starting simulation...")

    threads = []

    for code in registration_codes:
        simulator = ContenderSimulator(code)
        x = threading.Thread(target=simulator.simulate)
        x.start()
        threads.append(x)

    for thread in threads:
        thread.join()


class SimulatorException(Exception):
    pass


class Action(Enum):
    AddTick = 1
    RemoveTick = 2
    SwitchClass = 3


class ContenderSimulator(object):

    def __init__(self, registration_code):
        self.registration_code = registration_code
        self.problems_todo = []
        self.problems_ticked = []
        self.ticks = dict()
        self.contender = None
        self.contest = None
        self.comp_classes = []

    def request(self, method, path, body=None, params=None):
        headers = {"Authorization": "Regcode %s" % (self.registration_code,)}
        response = requests.request(method, url=(BASE_URL + path), headers=headers, json=body, params=params)

        if response.status_code in [200, 201, 204]:
            return response.json() if response.text else None
        else:
            try:
                error = response.json()["message"]
            except:
                error = None

            message = "%s %s => %d %s" % (method, path, response.status_code, error)
            raise SimulatorException(message)

    def simulate(self):
        global DELAY_MULTIPLIER, PLEASE_EXIT

        self.load_data()
        self.enter_contest()

        actions = [Action.AddTick] * 50 + [Action.RemoveTick] * 50 + [Action.SwitchClass] * 1

        while not PLEASE_EXIT:
            total_sleep = random.random() * DELAY_MULTIPLIER
            while total_sleep > 0 and not PLEASE_EXIT:
                time.sleep(1.0)
                total_sleep -= 1.0

            action = random.choice(actions)

            if action == Action.RemoveTick:
                removed_problem = self.remove_tick()
                if removed_problem:
                    self.log("Removed tick for problem %d" % (removed_problem,))
            elif action == Action.AddTick:
                added_problem = self.add_tick()
                if added_problem:
                    self.log("Added tick of problem %d" % (added_problem,))
            elif action == Action.SwitchClass:
                comp_class = self.switch_class()
                self.log("Changed class to %s" % (comp_class["name"]))

    def log(self, message):
        print("[%s] %s" % (self.registration_code, message))

    def load_data(self):
        self.contender = self.request("GET", "/contender/findByCode", params=dict(code=self.registration_code))
        self.comp_classes = self.request("GET", "/compClass")

        for tick in self.request("GET", "/tick"):
            problem_id = tick["problemId"]
            self.ticks[problem_id] = tick
            self.problems_ticked.append(problem_id)

        for problem in self.request("GET", "/problem"):
            problem_id = problem["id"]
            if problem_id not in self.problems_ticked:
                self.problems_todo.append(problem_id)

    def enter_contest(self):
        global FAKE_NAMES

        self.contender["name"] = get_fake_name()
        self.log("Picked name %s" % (self.contender["name"],))

        comp_class = random.choice(self.comp_classes)
        self.contender["compClassId"] = comp_class["id"]
        self.request("PUT", "/contender/%d" % (self.contender["id"],), self.contender)

        self.contest = self.request("GET", "/contest/%d" % (self.contender["contestId"],))
        self.log("Joining contest %s as %s" % (self.contest["name"], comp_class["name"]))

    def remove_tick(self):
        if len(self.problems_ticked) == 0:
            return None

        problem_id = random.choice(self.problems_ticked)

        tick = self.ticks[problem_id]
        self.request("DELETE", "/tick/%d" % (tick["id"],))

        del self.ticks[problem_id]
        self.problems_ticked.remove(problem_id)
        self.problems_todo.append(problem_id)

        return problem_id

    def add_tick(self):
        if len(self.problems_todo) == 0:
            return None

        problem_id = random.choice(self.problems_todo)

        tick = self.request("POST", "/tick", dict(
            contenderId=self.contender["id"],
            problemId=problem_id,
            isFlash=random.random() > 0.5))

        self.problems_todo.remove(problem_id)
        self.problems_ticked.append(problem_id)
        self.ticks[problem_id] = tick

        return problem_id

    def switch_class(self):
        comp_class = random.choice(self.comp_classes)
        self.contender["compClassId"] = comp_class["id"]
        self.request("PUT", "/contender/%d" % (self.contender["id"],), self.contender)

        return comp_class


def get_fake_name():
    names = [
        "Tamela Flinchum",
        "Tonia Pickell",
        "Gillian Kotek",
        "Suzan Davisson",
        "Mikel Doerr",
        "Imelda Mannix",
        "Dot Dimuzio",
        "Hope Simoneau",
        "Christinia Markum",
        "Miguelina Rosati",
        "Lyn Pacelli",
        "Candis Gourd",
        "Roni Bryd",
        "Stephenie Spadafora",
        "Johnna Hebron",
        "Lucrecia Barefield",
        "Julieann Benda",
        "Joeann Lyles",
        "Lanell Stuhr",
        "Li Prentice",
        "Eryn Ruzicka",
        "Katlyn Becker",
        "Elizbeth Elsey",
        "Meri Hewlett",
        "Desmond Stiverson",
        "Kristie Gunter",
        "Della Robichaud",
        "Randal Finkbeiner",
        "Hugo Piehl",
        "Frederica Lamere",
        "Mia Feeley",
        "Marcell Lamb",
        "Olivia Koehn",
        "Hildred Monaghan",
        "Sherrill Fabian",
        "Petronila Coloma",
        "Kiley Beshears",
        "Ashely Greenly",
        "James Pascal",
        "Clara Wynkoop",
        "Georgianna Eberly",
        "Angelique Kessler",
        "Simonne Schwindt",
        "Shakita Maddox",
        "Tim Coster",
        "Gonzalo Israel",
        "Ozella Grunwald",
        "Cruz Coman",
        "Nieves Lamothe",
        "Wade Coberly",
        "Twanda Kottwitz",
        "Delena Barraza",
        "Lilliana Reinhardt",
        "Hui Bruemmer",
        "Shaquana Ciesla",
        "Jannette Royall",
        "Halina Mars",
        "Darci Kaye",
        "Kaitlin Kriss",
        "Tiara Sulzer",
        "Malvina Schutt",
        "Rashad Furniss",
        "Dollie Radcliffe",
        "Jacqualine Mosser",
        "Cortez Murdock",
        "Monte Cruzado",
        "Jose Hwang",
        "Althea Corona",
        "Kathryn Harting",
        "Coralie Glaude",
        "Hilario Branson",
        "Emma Keogh",
        "Cristina Stackpole",
        "Stanford Malson",
        "Ross Wallin",
        "Susanna Nachman",
        "Leopoldo Leeds",
        "Zora Dandridge",
        "Chris Molinar",
        "Kurtis Gaona",
        "Raven Zambrana",
        "Debbie Stmartin",
        "Drusilla Dabrowski",
        "Nicol Mcclaskey",
        "Juliane Radebaugh",
        "Edwina Parkey",
        "Eladia Weinberger",
        "Elijah Ahlstrom",
        "Waldo Soloman",
        "Luanna Sass",
        "Kaitlyn Bosh",
        "Rory Ory",
        "Paulette Liriano",
        "Penelope Mckernan",
        "Emmitt Capra",
        "Mae Heim",
        "Samira Langhorne",
        "Jeanett Legaspi",
        "Sharla Marson",
        "Isobel Earls",
        "Phil Thomson",
        "Vernice Sidoti",
        "Marquis Lindsay",
        "Blanch Ehret",
        "Brant Pilkenton",
        "Kathrine Kennelly",
        "Giovanni Caughman",
        "Eduardo Dame",
        "Sheila Sinner",
        "Marcelene Mcdonagh",
        "Ayanna Plants",
        "Larry Cyrus",
        "Cristy Meister",
        "Jeanie Marko",
        "Anibal Underdown",
        "Gregory Wolfgram",
        "Corrin Force",
        "Inez Brunn",
        "Doreen Czapla",
        "Isaac Romberg",
        "Lisette Shuford",
        "Breanna Boris",
        "Verena Fazzino",
        "Kristin Palomares",
        "Sherril Berthiaume",
        "Minerva Nieto",
        "Herlinda Bishop",
        "Ernestina Overfield",
        "Lorie Duffie",
        "Theo Churchill",
        "Jillian Colley",
        "Kirk Daoust",
        "Junita Tezeno",
        "Kayleen Mcfaul",
        "Debera Kensinger",
        "Enola Ballengee",
        "Mitzie Ruis",
        "Deirdre Follette",
        "Tarsha Kloster",
        "Manuela Crepeau",
        "Carmelita Traynor",
        "Corie Fyffe",
        "Tonya Dory",
        "Lorenzo Rieck",
        "Aleen Shaw",
        "Danielle Dansie",
        "Paula Stringham",
        "Tomas Ruple",
        "Meggan Belcher",
        "Luna Ramm",
        "Annabell Roda",
        "Shalonda Delgiudice",
        "Dusty Zeck",
        "Paz Verde",
        "Kent Unknow",
        "Dale Millwood",
        "Sonya Notter",
        "Carl Mero",
        "Norah Dowdell",
        "Meta Pucci",
        "Aracelis Grover",
        "Shella Jardine",
        "Kandice Forman",
        "Joy Bakken",
        "Timmy Eckler",
        "Meggan Andreotti",
        "Lavonia Lummus",
        "Elnora Koontz",
        "Rolande Sack",
        "Nereida Zerr",
        "Rogelio Bennett",
        "Rachele Heintz",
        "Chassidy Reamer",
        "Eugenia Placencia",
        "Janett Holaday",
        "Lissette Lunt",
        "Michelina Theodore",
        "Salvador Mehta",
        "Myrtie Beal",
        "Johnnie Macek",
        "Janay Garriga",
        "Vernon Kampen",
        "Kayce Byington",
        "Richard Blas",
        "Astrid Labat",
        "Kathlyn Staple",
        "Arlette Sternberg",
        "Calista Ardoin",
        "Bonita Kepler",
        "Enriqueta Right",
        "Janeen Pogue",
        "Jenna Glandon",
        "Kandra Armstong",
        "Wilson Liedtke",
        "Aida Fowles",
        "Rheba Steimle",
        "Roger Doud",
        "Nena Yohn",
        "Antoinette Vancleve",
        "Carmine Garr",
        "Elmer Bernhard",
        "Kasey Aldana",
        "Raymundo Rumble",
        "Easter Dalpiaz",
        "Miki Uhler",
        "Arnoldo Starns",
        "Floyd Blasi",
        "Carlena Laughter",
        "Marti Mars",
        "Tonisha Schwartzman",
        "Ila Andreas",
        "Shella Sluss",
        "Mittie Hemmer",
        "Cherise Espy",
        "Denae Mota",
        "Alene Vos",
        "Geraldo Starkes",
        "Rosalina Tsuji",
        "Stefan Almquist",
        "Jennifer Hall",
        "Anita Clowers",
        "Javier Bardin",
        "Nellie Wassink",
        "Leone Debow",
        "Shayna Wahl",
        "Pricilla Rawling",
        "Orville Obregon",
        "Ladawn Morello",
        "Casimira Mathias",
        "Debbra Kimbler",
        "Etsuko Rotz",
        "Alysha Nachman",
        "Ressie Brophy",
        "Latonya Burk",
        "Kristine Lyford",
        "Consuela Hazen",
        "Williemae Leja",
        "Bryon Nicola",
        "Frankie Drummer",
        "Ossie Lobb",
        "Kami Leber",
        "Damian Kraemer",
        "Dusti Matley",
        "Trudy Lipsey",
        "Shonna Eastwood",
        "Marin Bull",
        "Lila Sisemore",
        "Ilda Langer",
        "Marvel Michelle",
        "Simone Dudding",
        "Maira Laramore",
        "Hermelinda Rupp",
        "Luisa Born",
        "Anisa Hagen",
        "Madonna Ropp",
        "Shelba Heffner",
        "Delbert Senegal",
        "Brice Jaynes",
        "Lashay Dill",
        "Annabell Riner",
        "Anneliese Slaughter",
        "Nida Jemison",
        "Jacinto Pleas",
        "Tamie Altom",
        "Bert Petrus",
        "Dotty Furey",
        "Gretchen Griffie",
        "Krystina Coger",
        "Ernest Scovil",
        "Lauralee Hinderliter",
        "Heriberto Flannigan",
        "Kimi Dudding",
        "Racquel Friedman",
        "Ana Koeller",
        "Janel Bogen",
        "Clifford Condie",
        "Kirby Diebold",
        "Jake Mcnicholas",
        "Silvia Sproull",
        "Chasity Barthel",
        "Sheryll Wulf",
        "Kiana Wess",
        "Felica Hoefer",
        "Rex Champlin",
        "Julienne Wise",
        "Ivy Huizar",
        "Keira Terrell",
        "Virgil Tan",
        "Ok Wishart",
        "Louann Kidd",
        "Marva Lagrone",
        "Idalia Wiltz",
        "Willena Perryman",
        "Khadijah Ardis",
        "Tomeka Hoffman",
        "Lyda Livers",
        "Gregoria Perrodin",
        "Ngoc Antonucci",
        "Shaquita Feltner",
        "Perry Jowett"
    ]

    return random.choice(names)


if __name__ == "__main__":
    main()
