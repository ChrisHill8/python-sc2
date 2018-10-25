import random

import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY
from sc2.player import Bot, Computer


class SentdeBot(sc2.BotAI):
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 66

    async def on_step(self, iteration):
        # what to do every step
        self.iteration = iteration
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.offensive_buildings()
        await self.build_army()
        await self.attack()

    async def build_workers(self):
        if self.units(PROBE).amount < self.units(NEXUS).amount * 22:
            if self.units(PROBE).amount < self.MAX_WORKERS:
                for nexus in self.units(NEXUS).ready.noqueue:
                    if self.can_afford(PROBE):
                        await self.do(nexus.train(PROBE))

    async def build_pylons(self):
        if self.supply_left < (self.supply_cap / 10) + 3 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.first)

    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(9.0, nexus)
            for vespene in vespenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                    # gives AttributeError: 'NoneType' object has no attribute 'closest'
                    # worker = self.select_build_worker(nexus)
                    # mf = self.state.mineral_field.closest_to(worker)
                    # worker.gather(mf)
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene))

    async def expand(self):
        if self.supply_used > (self.units(NEXUS).amount * 35) and self.can_afford(NEXUS) and not self.already_pending(
                NEXUS):
            await self.expand_now()

    async def offensive_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            if self.units(GATEWAY).amount == 0:
                if not self.already_pending(GATEWAY):
                    await self.build_gateway(pylon)
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)
            elif self.units(CYBERNETICSCORE).ready.exists:
                if self.units(STARGATE).amount == 0:
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        await self.build(STARGATE, near=pylon)
            elif self.minerals > 600:
                print('over 600 minerals')
                if self.units(GATEWAY).amount > self.units(STARGATE).amount:
                    await self.build_gateway(pylon)
                else:
                    if self.can_afford(STARGATE):
                        await self.build(STARGATE, near=pylon)

    async def build_gateway(self, pylon):
        if self.can_afford(GATEWAY):
            await self.build(GATEWAY, near=pylon)

    async def build_army(self):
        if self.units(CYBERNETICSCORE).ready:
            for stargate in self.units(STARGATE).ready.noqueue:
                if self.can_afford(VOIDRAY) and self.supply_left > 1:
                    await self.do(stargate.train(VOIDRAY))
            for gateway in self.units(GATEWAY).ready.noqueue:
                if self.units(STARGATE).amount > 0 and \
                        not self.units(STALKER).amount > self.units(VOIDRAY).amount + 5:
                    if self.can_afford(STALKER) and self.supply_left > 1:
                        await self.do(gateway.train(STALKER))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def attack(self):
        # {UNIT: [n to fight, n to defend]}
        aggressive_units = {STALKER: [11, 3],
                            VOIDRAY: [5, 1]}

        for UNIT in aggressive_units:
            if self.units(UNIT).amount > aggressive_units[UNIT][0] and \
                    self.units(UNIT).amount > aggressive_units[UNIT][1]:
                for s in self.units(UNIT).idle:
                    await self.do(s.attack(self.find_target(self.state)))

            elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
                if len(self.known_enemy_units) > 0:
                    for s in self.units(UNIT).idle:
                        await self.do(s.attack(random.choice(self.known_enemy_units)))


run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, SentdeBot()),
    Computer(Race.Terran, Difficulty.Hard)
], realtime=False)
