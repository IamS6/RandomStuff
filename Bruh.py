import random
import time


class Character:
    def __init__(self, name, hp, atk, defense, special, passive):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.special = special
        self.passive = passive
        self.special_meter = 0
        self.crit_rate = 5
        self.crit_damage = 1.5
        self.guardStatus = 0
        self.shield = 0
        self.buffs = {}
        self.debuffs = {}

    def take_damage(self, target, dmg, true_damage=False):
        if true_damage:
            effective_dmg = dmg
            self.hp = max(self.hp - effective_dmg, 0)
            return effective_dmg

        # ------------- Not True Damage
        UsedDef = self.defense + (
            self.buffs.get("Defense Boost", {"value": 0})["value"] if "Defense Boost" in self.buffs else 0)
        if "Armor Break" in self.debuffs:
            UsedDef -= int(self.defense * min((0.2 * self.debuffs["Armor Break"].get('stacks', 0)), 1))
        if "Dead Eye" in target.buffs:
            UsedDef -= int(self.defense * 0.5)
        def_val = random.randint(UsedDef, UsedDef + 10)

        effective_dmg = max(dmg - def_val, 0)

        if "Guard Break" in self.debuffs:
            GB = random.randint(1, 5) <= 1
            if GB:
                effective_dmg = max(dmg, 0)

        if self.guardStatus == 1:
            print(f"{self.name} blocked and will only taking half damage!")
            effective_dmg = effective_dmg // 2

        if self.shield > 0:
            if effective_dmg <= self.shield:
                self.shield -= effective_dmg
                effective_dmg = 0
            else:
                effective_dmg -= self.shield
                self.shield = 0

        self.hp = max(self.hp - effective_dmg, 0)
        return effective_dmg

    def calculate_damage(self, target):

        calc_atk = self.atk
        if "Yuri" in self.name:
            calc_atk += self.passive(self)

        if "Cripple" in self.debuffs:
            calc_atk //= 2

        if hasattr(self, "Element") and "Hydro" in self.Element:
            calc_atk += int(self.max_hp * 0.5 * self.EleCrystal)

        # Damage value
        calc_atk = calc_atk + (
            self.buffs.get("Attack Boost", {"value": 0})["value"] if "Attack Boost" in self.buffs else 0)
        base_damage = random.randint(calc_atk, calc_atk + 20)

        # Critical hit check
        crit_chance = self.crit_rate + self.buffs.get("Critical Rate Boost", {"value": 0})["value"]
        if self.buffs.get("Precision", {"value": 0})["value"] > 0:
            crit_chance = 100
        is_crit = random.randint(1, 100) <= crit_chance
        if is_crit:
            base_damage = int(base_damage * (self.crit_damage + self.buffs.get("Critical Damage Boost", {"value": 0})[
                "value"]))  # Critical hit multiplier

        # Damage mult
        mult = 1.0
        if hasattr(self, "Star_marks"):
            mult += 0.08 * self.Star_marks

        if "Entanglement" in self.debuffs:
            mult -= 0.6

        if hasattr(self, "Element") and "Electro" in self.Element:
            mult += (0.5 * self.EleCrystal)

        if getattr(self, "Nightfall", False) and hasattr(self, "Twilight"):
            mult += 0.1 * self.Twilight

        if getattr(target, "Nightfall", False) and hasattr(target, "Twilight"):
            mult += 0.1 * target.Twilight

        if getattr(self, "MoonGlow", True):
            mult += 0.5

        if getattr(self, "Strike", True) and hasattr(self, "Rage"):
            mult += 0.01 * self.Rage

        base_damage = int(base_damage * mult)
        return base_damage, is_crit

    def attack(self, target):
        if "Stun" in self.debuffs or "Freeze" in self.debuffs:
            print(f"{self.name} is stunned and cannot attack!")
            return

        damage, is_crit = self.calculate_damage(target)
        if hasattr(self, "MoonGlow") and self.MoonGlow == True:
            actual_damage = target.take_damage(self, damage, true_damage=True)
        else:
            actual_damage = target.take_damage(self, damage)


        if is_crit:
            print(f"{self.name} landed a CRITICAL HIT! Dealt {actual_damage} damage to {target.name}.")
        else:
            print(f"{self.name} attacked {target.name}, dealing {actual_damage} damage.")

        if "Entanglement" in self.debuffs and random.random() >= 0.4:
            print(
                f"Entanglement is in effect! {self.name} attacks once again, dealing {actual_damage} to {target.name}!")
            target.take_damage(self, damage)

        if hasattr(self, "Elements") and "Dendro" in self.Element:
            if random.random() <= 0.07 * self.EleCrystal:
                print(
                    f"Dendro infusion in effect! {self.name} attacks 2 more times! dealing a total of {actual_damage} to {target.name}!")
                target.take_damage(self, damage * 2)

        # -------- thorns
        if "S-Thorn" in target.buffs:
            reflect = int(0.1 * target.EleCrystal * actual_damage)
            print(f"{target.name}'s Thorns reflected {reflect} damage back!")
            self.take_damage(target, reflect)

        # --------- Quake
        if "Quake" in target.buffs:
            reflect = int(0.9 * target.shield)
            print(f"{target.name}'s Quake dealt {reflect} damage!")
            self.take_damage(target, reflect, true_damage=True)

        if self.name in ["Akane", "Arona"]:
            self.passive(self, actual_damage, target)
        elif self.name in ["Cosmos"]:
            self.passive(self)
        elif self.name in ["Aria"]:
            self.passive(self, target, self.special_meter)

        if self.name in ["Lily"]:
            self.passive(self, target)
        if "Lifesteal" in self.buffs:
            gained_hp = int(actual_damage * self.buffs.get("Lifesteal", {"value": 0})["value"])
            self.hp += gained_hp
            print(f"{self.name} stole {gained_hp} as healing!")

    def apply_buff(self, buff_name, value, duration):
        self.buffs[buff_name] = {'value': value, 'duration': duration}

    def apply_debuff(self, debuff_name, duration):
        """Applies a debuff, handling DoTs separately."""

        if debuff_name in ["Poison", "Burn", "Bleed"]:
            if "DoT" not in self.debuffs:
                self.debuffs["DoT"] = {"duration": {}, "stacks": {}} 

            if debuff_name in self.debuffs["DoT"]["duration"]:
                self.debuffs["DoT"]["duration"][debuff_name] = max(
                    self.debuffs["DoT"]["duration"][debuff_name], duration
                ) 
            else:
                self.debuffs["DoT"]["duration"][debuff_name] = duration

            if debuff_name == "Bleed":
                self.debuffs["DoT"]["stacks"][debuff_name] = min(
                    10, self.debuffs["DoT"]["stacks"].get(debuff_name, 0) + 1)
            self.debuffs["DoT"]["duration"][debuff_name] = duration
        else:
            if debuff_name not in self.debuffs:
                self.debuffs[debuff_name] = {"duration": duration, "stacks": 1}
            else:
                if debuff_name == "Armor Break":
                    self.debuffs[debuff_name]["stacks"] = min(self.debuffs[debuff_name]["stacks"] + 1, 5)
                    self.debuffs[debuff_name]["duration"] = max(self.debuffs[debuff_name]["duration"], duration)
                else:
                    self.debuffs[debuff_name]["duration"] = max(self.debuffs[debuff_name]["duration"], duration)

    def process_effect(self):
        """Reduces buff and debuff durations, removing expired ones."""

        # Separate lists for expired buffs and debuffs
        expired_debuffs = []
        expired_buffs = []

        # Process Debuffs
        for key in list(self.debuffs.keys()):
            if key == "DoT":
                continue

            self.debuffs[key]["duration"] -= 1
            if self.debuffs[key]["duration"] == 0:
                expired_debuffs.append(key)

        # Process Buffs
        for key in list(self.buffs.keys()):
            self.buffs[key]["duration"] -= 1
            if self.buffs[key]["duration"] == 0:
                expired_buffs.append(key)

        # Remove expired debuffs and buffs
        for key in expired_debuffs:
            del self.debuffs[key]

        for key in expired_buffs:
            del self.buffs[key]

    def process_DoT(self, target):
        if "DoT" not in self.debuffs:
            return

        expired_dot = []
        total_damage = 0

        for DoT in list(self.debuffs["DoT"]["duration"].keys()):
            damage = 0

            if DoT == "Poison":
                damage += max(1, min(target.atk // 4, int(self.max_hp * 0.07)))
            elif DoT == "Burn":
                damage += max(1, self.max_hp // 10)
            elif DoT == "Bleed":
                damage += max(1, (target.atk // 20) * self.debuffs["DoT"]["stacks"].get("Bleed", 1))

            total_damage += damage
            self.hp -= total_damage
            print(f"{self.name} took {total_damage} damage from {DoT}!")

            # Reduce duration
            self.debuffs["DoT"]["duration"][DoT] -= 1

            # If DoT expires, mark it for removal
            if self.debuffs["DoT"]["duration"][DoT] <= 0:
                expired_dot.append(DoT)

        for DoT in expired_dot:
            del self.debuffs["DoT"]["duration"][DoT]
            self.debuffs["DoT"].pop(DoT, None)

            if "Bleed" not in self.debuffs["DoT"]["duration"] and "stacks" in self.debuffs["DoT"]:
                self.debuffs["DoT"]["stacks"].pop("Bleed", None)

        if not self.debuffs["DoT"]["duration"]:
            del self.debuffs["DoT"]

    # Special usage
    def use_special(self, target):
        minimal_charge = {
            "Yuri": 100,
            "Akane": 100,
            "Imakaze": 75,
            "Cosmos": 80,
            "Aria": 50,
        }

        charge_cap = {
            "Yuri": 300,
            "Akane": 300,
            "Imakaze": 150,
            "Cosmos": None,
            "Aria": 100
        }

        required_meter = minimal_charge.get(self.name, 100)
        if "Arona" in self.name:
            if self.Everday:
                required_meter = 250
            elif self.Nightfall:
                required_meter = 150
        max_charge = charge_cap.get(self.name, 300)

        if "Stun" in self.debuffs or "Freeze" in self.debuffs:
            print(f"{self.name} is stunned and cannot attack!")
            return

        if self.special_meter >= required_meter:
            charge_level = self.special_meter if max_charge is None else min(self.special_meter, max_charge)
            print(f"{self.name} unleashes a Special Attack with {charge_level}% charge!")
            self.special(self, target, charge_level)
            self.special_meter = 0
            return True
        else:
            print(f"{self.name} doesn't have enough special charge!")
            return False

    # Finalize turn
    def post_turn(self, target):
        charge_eff = {
            "Yuri": 1,
            "Akane": 1,
            "Imakaze": 0.7,
            "Cosmos": 0,
            "Aria": 0.4
        }
        charge_cap = {
            "Yuri": 300,
            "Akane": 300,
            "Imakaze": 150,
            "Cosmos": None,
            "Aria": 100
        }
        # -----------------------
        charge_efficiency = charge_eff.get(self.name, 1)
        charge_capacity = charge_cap.get(self.name, 300)
        self.process_DoT(target)
        self.process_effect()
        OriCharge = random.randint(10, 30)
        Charge = int(OriCharge * charge_efficiency)

        if "Freeze" in self.debuffs:
            Charge = 0
        if self.name in charge_eff:
            if charge_capacity is not None:
                self.special_meter = min(self.special_meter + Charge, charge_capacity)
            else:
                pass
        else:
            if "Kaede" in self.name and hasattr(self, "SolarFlare") and self.SolarFlare:
                self.special_meter += 50
            else:
                self.special_meter += 20
        self.guardStatus = 0

        if self.name in ["Kaede", "Lilith"]:
            self.passive(self, target)
        if self.name in ["Arona"]:
            self.special_meter += random.randrange(10, 30, 10)


# Yuri --------------
def Yuri_super(self, target, charge_level):
    print(f"{self.name} used her SPECIAL,", end="")
    UsedAtk = random.randint(self.atk, self.atk + 10)
    if charge_level >= 300:
        damage = UsedAtk * 13
        self.apply_buff("Attack Boost", 50, 5)
        self.apply_buff("Critical Rate Boost", 60, 5)
        self.apply_buff("Critical Damage Boost", 2, 5)
        print(f" Stealing {damage} HP and gained 70 Attack, 60% CRIT RATE, and 200% CRIT DMG for 5 turns!")
    elif charge_level >= 200:
        damage = UsedAtk * 7
        self.apply_buff("Attack Boost", 40, 4)
        self.apply_buff("Critical Rate Boost", 40, 4)
        self.apply_buff("Critical Damage Boost", 1, 4)
        print(f" Stealing {damage} HP and gained 40 Attack, 40% CRIT RATE, and 100% CRIT DMG for 4 turns!")
    else:
        damage = UsedAtk * 3
        self.apply_buff("Attack Boost", 20, 3)
        self.apply_buff("Critical Rate Boost", 25, 3)
        self.apply_buff("Critical Damage Boost", 0.5, 3)
        print(f" Stealing {damage} HP and gained 20 Attack, 25% CRIT RATE, and 50% CRIT DMG for 3 turns!")
    target.take_damage(self, damage, true_damage=True)
    self.hp = min(self.hp + damage, self.max_hp)


def Yuri_passive(self):
    """Gain ATK based on special meter."""
    bonus_atk = (self.max_hp - self.hp) // 2
    self.apply_buff("Lifesteal", 0.1, -1)
    return bonus_atk


# Yuri --------------

# Akane -------------
def Akane_super(self, target, charge_level):
    self.debuffs = {key: value for key, value in self.debuffs.items() if self.debuffs[key]["duration"] < 0}
    if "DoT" in self.debuffs:
        self.debuffs["DoT"]["duration"] = {
            key: value for key, value in self.debuffs["DoT"]["duration"].items() if value < 0
        }

        if "Bleed" not in self.debuffs["DoT"]["duration"] and "stacks" in self.debuffs["DoT"]:
            del self.debuffs["DoT"]["stacks"]["Bleed"]

        if not self.debuffs["DoT"]["duration"]:
            del self.debuffs["DoT"]
    target.apply_debuff("Poison", duration=3)
    print("Removed all debuffs,", end=" ")
    if charge_level >= 300:
        heal = min(self.hp + 350, self.max_hp)
        self.hp = heal
        self.apply_buff("Defense Boost", 100 + (10 if "Reckoning" not in self.buffs else 20) * self.Revelation, 3)
        print(
            f"healed 350 HP, and gained {100 + (10 if 'Reckoning' not in self.buffs else 20) * self.Revelation} DEF for 3 turns!")
    elif charge_level >= 200:
        self.hp = min(self.hp + 200, self.max_hp)
        self.apply_buff("Defense Boost", 60 + (10 if "Reckoning" not in self.buffs else 20) * self.Revelation, 3)
        print(
            f"healed 200 HP, and gained {60 + (10 if 'Reckoning' not in self.buffs else 20) * self.Revelation} DEF for 3 turns!")
    else:
        self.hp = min(self.hp + 100, self.max_hp)
        self.apply_buff("Defense Boost", 30 + (10 if "Reckoning" not in self.buffs else 20) * self.Revelation, 3)
        print(
            f"healed 100 HP, and gained {30 + (10 if 'Reckoning' not in self.buffs else 20) * self.Revelation} DEF for 3 turns!")


def Akane_passive(self, damageDealt, target):
    if not hasattr(self, "Revelation"):
        self.Revelation = 0

    if damageDealt <= 40 + (10 * self.Revelation):
        self.Revelation += 1
        print("Gained a stack of revelation!")

    if self.Revelation >= 10 and "Reckoning" not in self.buffs:
        self.apply_buff("Reckoning", 0, -1)
        print("Gained Reckoning!")

    if self.Revelation > 0:
        self.apply_buff("Attack Boost", (5 if "Reckoning" not in self.buffs else 10) * self.Revelation, -1)

    if "Reckoning" in self.buffs:
        chance = random.random()
        if chance <= 0.75:
            target.apply_debuff("Stun", 2)


# Akane -------------

# Imakaze -----------
def Imakaze_super(self, target, charge_level):
    if not hasattr(self, "Integration"):
        self.Integration = 0

    usedPoints = charge_level
    for i in range(self.Integration + 1):
        P1 = random.randint(1, usedPoints)
        P2 = usedPoints - P1

        self.atk += P1
        self.hp += P1
        self.defense += P2
        target.hp -= P2

        print(f"Gained {P1} ATK and {P2} DEF. Healed {P1} HP and dealt {P2} as TRUE DAMAGE!")
        if i < self.Integration:
            print("Imakaze's SPECIAL triggers once more!")

    self.passive(self)


def Imakaze_passive(self):
    if not hasattr(self, "Integration"):
        self.Integration = 0
    self.Integration = min(self.Integration + 1, 3)
    self.special_meter += 10 * self.Integration


# Imakaze -----------

# Cosmos ------------

def Cosmos_super(self, target, charge_level):
    mult = 1 + 0.08 * self.Star_marks
    RestorationType = random.randint(1, 3)
    Restoration = int(self.StarSacrificialValue * mult)
    if RestorationType == 1:
        self.max_hp += Restoration
        self.hp += Restoration
        print(f"Increased MAX HP ", end="")
    elif RestorationType == 2:
        self.atk += Restoration
        print(f"Increased ATK ", end="")
    elif RestorationType == 3:
        self.defense += Restoration
        print(f"Increased DEF ", end="")

    print(f"by {Restoration}", end="")
    if self.Star_marks >= 8:
        debuff_list = ["Guard Break", "Armor Break", "Cripple", "Burn", "Bleed", "Poison"]
        Inflict = random.choice(debuff_list)
        target.apply_debuff(Inflict, 3)
        print(f" and inflicted {Inflict} on {target.name} for 3 turns!")
    else:
        print("!")
    self.Star_marks = 0
    self.StarSacrificialValue = 0


def Cosmos_passive(self):
    if not hasattr(self, "Star_marks"):
        self.Star_marks = 0
        self.StarSacrificialValue = 0

    Sacrificial = 0

    SacrificialType = random.randint(1, 3)
    if SacrificialType == 1:
        Sacrificial = int(self.hp * 0.08)
        self.hp -= Sacrificial
        self.StarSacrificialValue += Sacrificial
    elif SacrificialType == 2:
        Sacrificial = int(self.atk * 0.08)
        self.atk -= Sacrificial
        self.StarSacrificialValue += Sacrificial
    elif SacrificialType == 3:
        Sacrificial = int(self.defense * 0.08)
        self.defense -= Sacrificial
        self.StarSacrificialValue += Sacrificial

    self.Star_marks += 1
    self.special_meter = self.StarSacrificialValue

    print(f"{self.name} gains a Star Mark!")


# Cosmos ------------

# Aria ------------

def Aria_super(self, target, charge_level):
    Library = ["Dendro", "Pyro", "Hydro", "Cryo", "Anemo", "Geo", "Electro"]
    SelectEle = random.choice(Library)
    if "None" in self.Element:
        print(f"Gained an Elemental Variable! Your weapon is now infused with {SelectEle}!")
    else:
        print(f"Swapped your Elemental Variable! Your weapon is now infused with {SelectEle}!")
    if not hasattr(self, "EleCrystal"):
        self.EleCrystal = 0
    if not hasattr(self, "EleShard"):
        self.EleShard = 0

    print("Gained an Elemental Crystal!")

    self.Element = SelectEle
    self.EleCrystal += 1
    heal = self.max_hp // 2
    self.hp = min(self.hp + heal, self.max_hp)

    print(f"Healed for {heal} HP!")
    if "Anemo" in self.Element:
        self.apply_buff("Defense Boost", self.defense * (0.5 + self.EleCrystal))
        print("Increased Defense and MAX HP, ATK, and DEF will consecutively increase!")

    elif "Geo" in self.Element:
        value = int(self.max_hp * 0.5 + (0.1 * self.EleCrystal))
        self.shield += value
        print(f"Gained Quake and {value} shield, and Quake for the duration of this infusion!")

    elif "Pyro" in self.Element:
        print("Increased ATK and attacks can now inflict BURN!")

    elif "Hydro" in self.Element:
        print("MAX HP will siginificantly consecutively increase and will deal increased DAMAGE based on MAX HP!")

    elif "Cryo" in self.Element:
        print("Increased CRIT RATE and CRIT DAMAGE and attacks have a chance to inflict FREEZE")

    elif "Dendro" in self.Element:
        self.apply_buff("S-Thorn", 0, 2)

    elif "Electro" in self.Element:
        if random.random() <= 0.07 * self.EleCrystal:
            extra = int(self.atk * 3 + (0.7 * self.EleCrystal))
            actual = target.take_damage(self, extra)
            print(f"Electro infusion in effect! dealt {actual} extra damage to {target.name}!")

    self.passive(self, target, charge_level)


def Aria_passive(self, target, charge_level):
    if not hasattr(self, "Element"):
        self.Element = "None"
    if not hasattr(self, "EleCrystal"):
        self.EleCrystal = 0
    if not hasattr(self, "EleShard"):
        self.EleShard = 0

    if "Anemo" in self.Element:
        add = 3 * self.EleCrystal
        self.atk += add
        self.defense += add
        self.max_hp += add
        print(f"Increased ATK, DEF, and MAX HP by {add}!")

    elif "Geo" in self.Element:
        shield = int(self.max_hp * (0.1 + 0.02 * self.EleCrystal))
        self.shield += shield
        print(f"Gained {shield} shield!")
        self.apply_buff("Quake", 0, 1)
        print("")
        if "Quake" in self.buffs:
            reflect = int(0.9 * self.shield)
            print(f"{self.name}'s Quake dealt {reflect} damage!")
            target.take_damage(self, reflect, true_damage=True)

    elif "Pyro" in self.Element:
        self.apply_buff("Attack Boost", int(self.atk * 0.5 * self.EleCrystal), 2)
        if random.random() <= 0.07 * self.EleCrystal:
            print("Inflicted Burn for 3 turns!")
            target.apply_debuff("Burn", 3)

    elif "Hydro" in self.Element:
        self.max_hp = int(self.max_hp + (self.max_hp * (0.1 * self.EleCrystal)))

    elif "Cryo" in self.Element:
        self.apply_buff("Critical Rate Boost", 10 * self.EleCrystal, 2)
        self.apply_buff("Critical Damage Boost", 0.5 * self.EleCrystal, 2)
        if random.random() <= 0.07 * self.EleCrystal:
            print("Inflicted Freeze for 3 turns!")
            target.apply_debuff("Freeze", 3)

    elif "Dendro" in self.Element:
        self.apply_buff("S-Thorn", 0, 2)

    elif "Electro" in self.Element:
        if random.random() <= 0.07 * self.EleCrystal:
            extra = int(self.atk * 3 + (0.7 * self.EleCrystal))
            actual = target.take_damage(self, extra)
            print(f"Electro infusion in effect! dealt {actual} extra damage to {target.name}!")

    ShardChance = random.randint(1, max(charge_level, 2))
    gained = 0
    if "None" not in self.Element:
        if ShardChance >= 25:
            gained += 1
            self.EleShard += 1
        if ShardChance >= 50:
            gained += 1
            self.EleShard += 1
        if ShardChance >= 75:
            gained += 1
            self.EleShard += 1
    if gained > 0:
        print(f"Gained {gained} shard{'s!' if gained > 1 else '!'}")

    if hasattr(self, "EleShard") and hasattr(self, "EleCrystal") and self.EleShard >= 7:
        self.EleShard -= 7
        self.EleCrystal += 1
        print(f"Gained an Elemental Crystal!")


# Enemies' Special
# Easy
def Super_E1(self, target, charge):
    mult = random.randint(3, 5)
    self.atk *= mult
    print(f"{self.name} used her special! Her own ATK is increased by {mult}-fold for this turn!")
    self.attack(target)
    self.atk = int(self.atk / mult)


def Super_E2(self, target, charge):
    self.apply_buff("Defense Boost", 50, 2)
    CurrDef = (self.defense + self.buffs.get("Defense Boost", {"value": 0})["value"])
    E2HealPoints = random.randint(CurrDef // 2, CurrDef * 2)
    self.hp += E2HealPoints
    print(f"{self.name} used her special! Increased her own DEF by 50 and healed herself for {E2HealPoints}!")


def Super_E3(self, target, charge):
    target.apply_buff("Defense Boost", 20, 3)
    BuffApply = random.randint(1, 2)
    print("Gained", end=" ")
    if BuffApply == 1:
        self.apply_buff("Dead Eye", 0, 3)
        print("Dead Eye", end=" ")
    elif BuffApply == 2:
        self.apply_buff("Precision", 0, 3)
        print("Precision", end=" ")

    print("for 3 turns and gave the enemy 20 DEF boost for 2 turns!")


# Normal
def Super_N1(self, target, charge):
    count = 2
    hit = 0

    while count > 0 and hit < 10:
        damage = random.randint(5, 10 + hit)
        target.take_damage(self, damage, true_damage=True)
        print(f"{self.name} triggered Quantum Cascade, dealing {damage} damage to {target.name}!")
        time.sleep(0.1)
        hit += 1
        count -= 1

        chance = random.random()
        if chance >= 0.5 and hit < 10:
            print("Quantum Fission in effect!")
            count += 2

    if hit >= 5:
        target.apply_debuff("Entanglement", 3)
        print(f"Inflicted Entanglement to {target.name} for 3 turns!")


def Super_N2(self, target, charge_value):
    if not hasattr(self, "SpecialCount"):
        self.SpecialCount = 0
    if not hasattr(self, "HPTreshold"):
        self.HPTreshold = self.max_hp
    self.SpecialCount += 1
    if not self.SolarFlare:
        heal = int(0.7 * (self.HPTreshold - self.hp))
        self.hp = min(self.hp + heal, self.max_hp)
        self.HPTreshold = self.hp
        Threshold = heal
        Mult = min(0.3 + 0.1 * self.SpecialCount, 2)
        damage = int(Threshold * Mult)
        target.take_damage(self, damage, true_damage=True)
        print(f"Healed for {heal} HP and dealt {damage} damage to {target.name}!")
    elif self.SolarFlare:
        shield = 10 * self.SpecialCount
        self.shield += shield
        print(f"Gained {shield} shield!")


def Passive_N2(self, target):
    if not hasattr(self, "SolarFlare"):
        self.SolarFlare = False

    if self.hp <= self.max_hp * 0.3 and not self.SolarFlare:
        print(f"{self.name} has entered Solar Flare state, continuously burning {target.name}!")
        self.SolarFlare = True
        target.apply_debuff("Burn", -1)


def Super_N3(self, target, charge_value):
    mult = 1.5
    self.atk = int(self.atk * mult)
    self.attack(target)
    self.atk = int(self.atk / mult)

    print("Left 3 Rift marks!")

    target.rift += 3

    if target.rift >= 3:
        dmg = int((self.atk * 0.7 * target.rift) * (1 + (0.2 * target.rift)))
        print(f"The Rift marks explode, dealing {dmg} damage to {target.name}!")
        target.take_damage(self, dmg, true_damage=True)
        if target.rift >= 5:
            print(f"The explosion is too strong! {self.name} also received {dmg} damage!")
            self.take_damage(target, dmg, true_damage=True)
        target.rift = 0


def Passive_N3(self, target):
    if not hasattr(target, "rift"):
        target.rift = 0

    if random.random() <= 0.39:
        print("Left a Rift mark!")
        target.rift += 1

    if target.rift >= 3:
        dmg = int((self.atk * 0.7 * target.rift))
        print(f"The Rift marks explode, dealing {dmg} damage to {target.name}!")
        target.take_damage(self, dmg, true_damage=True)
        if target.rift >= 5:
            print(f"The explosion is too strong! {self.name} also received {dmg} damage!")
            self.take_damage(target, dmg, true_damage=True)
        target.rift = 0


def Super_H1(self, target, charge_value):
    if not hasattr(self, "Soul"):
        self.Soul = 0
    self.hp = min(self.hp + 100, self.max_hp)
    print("healed for 100 HP and gained a Soul mark!")
    self.Soul += 1


def Passive_H1(self, target):
    if self.hp <= 500 and not hasattr(target, "Doom"):
        defup = self.Soul * 50
        self.defense += defup
        init = max(20 - self.Soul, 1)
        target.Doom = init
        print(f"Consumed all soul marks and gained {defup}!")
        print(f"THE RITUAL HAS BEGUN.", end=" ")
    if hasattr(target, "Doom"):
        target.Doom -= 1
        print(f"{target.Doom} TURN{'S' if target.Doom > 1 else ''} LEFT UNTIL THE RITUAL IS COMPLETE.")
        if target.Doom == 0:
            print("YOUR END IS HERE.")
            target.hp = 0


def Super_H2(self, target, charge_value):
    if self.Nightfall and charge_value >= 150:
        self.Nightfall = False
        self.Everday = True
        self.hp //= 2
        self.max_hp //= 2
        heal = int(self.max_hp * 0.1)
        self.hp = min(self.hp + heal, self.max_hp)
        print(f"Entered the Everday state. Healed for {heal} HP and all stats are increased!")

    elif self.Everday and charge_value >= 250:
        self.Nightfall = True
        self.Everday = False
        self.max_hp *= 2
        self.hp = min(self.hp + self.max_hp // 2, self.max_hp)
        print("Entered the Nightfall state. Increased MAX HP by 100% and dreams are echoing...")


def Passive_H2(self, actual_damage, target):
    if not hasattr(self, "Nightfall"):
        self.Nightfall = False
    if not hasattr(self, "Everday"):
        self.Everday = True
    if not hasattr(self, "Threshold"):
        self.Threshold = 0
    if not hasattr(self, "Twilight"):
        self.Twilight = 0

    if self.Everday:
        self.apply_buff("Attack Boost", int(self.atk * 0.75), 1)
        self.apply_buff("Defense Boost", int(self.defense * 0.75), 1)
        self.apply_buff("Critical Rate Boost", 50, 1)
        self.apply_buff("Critical Damage Boost", 1, 1)
        if random.random() <= 0.5:
            heal = actual_damage // 2
            print(f"Healed for {heal} HP!")
            self.hp = min(self.hp + heal, self.max_hp)

    elif self.Nightfall:
        missing = self.max_hp - self.hp
        new_twilight = missing // int(self.max_hp * 0.05)  # 1 stack per 5% missing HP

        if new_twilight != self.Twilight:
            change = new_twilight - self.Twilight
            self.Twilight = new_twilight
            if change > 0:
                print(f"Gained {change} stack{'s' if change > 1 else ''} of Twilight!")
            else:
                print(f"Lost {abs(change)} stack{'s' if abs(change) > 1 else ''} of Twilight!")

def Super_H3(self, target, charge_value):
    if not hasattr(self, "Spirit"):
        self.Spirit = 0

    if self.Spirit >= 5:
        self.Spirit = 5
    else:
        self.Spirit += 1
    print(f"Gained a Spirit! {self.name} now has {self.Spirit} Spirit{'s' if self.Spirit > 1 else ''}!")

def Passive_H3(self, target):
    if not hasattr(self, "HPtreshold"):
        self.HPtreshold = self.hp

    if not hasattr(self, "Spirit"):
        self.Spirit = 0

    self.apply_buff("Attack Boost", self.Spirit * 5, -1)
    self.apply_buff("Defense Boost", self.Spirit * 5, -1)

    # Exploding spirit
    damage_taken = self.HPtreshold - self.hp
    self.HPtreshold = self.hp
    if not hasattr(self, "Undead") and self.Spirit > 0 and damage_taken > 100:
        self.Spirit -= 1
        damage = random.randrange(30, 50)
        target.take_damage(self, damage, true_damage=True)
        target.apply_debuff("Cripple", duration=2)
        print(f"A spirit exploded! Dealt {damage} damage and inflicted CRIPPLE for 2 turns to {target.name}!")

    # Max spirit count
    if self.Spirit == 5:
        print(f"The spirits inflicted POISON to {target.name}!")
        target.apply_debuff("Poison", duration=1)

    if hasattr(self, "Undead"):
        self.special_meter = 0
        self.hp = self.hp - 100 if (self.hp - 50) > 0 else 1
        self.atk = self.atk - 5 if (self.atk - 5) > 0 else 1
        self.defense = self.hp - 5 if (self.hp - 5) > 0 else 1
        print("Lost HP, ATK, and DEF!")

    # Revival trigger
    if self.hp < 1 and not hasattr(self, "Undead"):
        self.hp = 1000
        self.atk += 15 * self.Spirit
        self.defense += 15 * self.Spirit
        self.Spirit = 0
        self.Undead = True
        print("Gained the power of undead! Healed for 1000 HP and gained spirit buffs that will decay overtime!")


def Super_H4(self, target, charge_value):
    if not hasattr(self, "MoonGlow"):
        self.MoonGlow = False

    if self.MoonGlow is False:
        self.shield = 500
        self.MoonGlow = True

    elif self.MoonGlow is True:
        self.atk += self.shield
        self.defense += self.shield
        self.shield = 500

def Passive_H4(self):
    if not hasattr(self, "MoonGlow"):
        self.MoonGlow = False

    if self.shield > 0:
        self.MoonGlow = True
    else:
        self.MoonGlow = False

def Super_I1(self, target, charge_value):
    if not hasattr(self, "Pride"):
        self.Pride = 0

    gain = random.randint(20, 30)
    self.Pride += gain
    target.take_damage(self,  gain * 10, true_damage=True)
    print(f"Gained {gain} Pride and dealt {gain * 10} Damage to {target.name}")

def Passive_I1(self):
    print("Test")
    if not hasattr(self, "Pride"):
        self.Pride = 30

    if not hasattr(self, "Rage"):
        self.Rage = 0

    if not hasattr(self, "Strike"):
        self.Strike = False

    converse = random.randint(5, 10)
    self.Pride -= converse
    self.Rage += converse

    if self.Rage >= 100:
        self.Strike = True

    self.Rage = 150 if self.Rage >= 150 else self.Rage

    print(f"Converted {converse} Pride into Rage!")
    print(f"Current Pride stack: {self.Pride}")
    print(f"Current Rage stack: {self.Rage}")
    self.apply_buff("Attack Boost", self.Rage, -1)
    self.apply_buff("Defense Boost", self.Pride, -1)

# ------ Programs

# Action selection
def SelfCurrentTurn(self, target, charge):
    charge_cap = {
        "Yuri": 300,
        "Akane": 300,
        "Imakaze": 150,
        "Cosmos": None,
        "Aria": 100
    }

    max_charge = charge_cap.get(self.name, 300)

    print("Select your action:")
    print("1. Attack")
    print("2. Guard")
    print(f"3. Special ({charge}" + (f"/{max_charge})" if max_charge is not None else ")"))
    turnEnd = False
    while not turnEnd:
        Select = int(input(">> "))
        if Select == 1:
            self.attack(target)
            turnEnd = True
        elif Select == 2:
            self.guardStatus = 1
            turnEnd = True
        elif Select == 3:
            hasUlted = self.use_special(target)
            if hasUlted:
                turnEnd = True
            else:
                pass


def EnemyTurn(self, target, charge):
    minimal_charge = {
        "Arona": 250,
    }
    useSpecial = minimal_charge.get(self.name, 100)
    if charge >= useSpecial:
        self.use_special(target)
    else:
        self.attack(target)


def Stats(self, target):
    print(f"Your HP :   {self.hp}/{self.max_hp} + ({self.shield})")
    print(
        f"""Your ATK:   {self.atk} + {(self.buffs.get("Attack Boost", {"value": 0})["value"] if "Attack Boost" in self.buffs else 0)}""")
    print(
        f"""Your DEF:   {self.defense} + {(self.buffs.get("Defense Boost", {"value": 0})["value"] if "Defense Boost" in self.buffs else 0)}""")
    if "Yuri" in self.name:
        print(f"Current passive ATK bonus: {(self.max_hp - self.hp) // 2}")
    elif "Akane" in self.name:
        print(f"Revelation stacks: {self.Revelation if hasattr(self, 'Revelation') else 0}")
        print(f"Reckoning effects: {'Inactive' if 'Reckoning' not in self.buffs else 'Active'}")
    elif "Imakaze" in self.name:
        print(f"Intagration stacks: {self.Integration if hasattr(self, 'Integration') else 0}")
    elif "Cosmos" in self.name:
        print(f"Star Mark stacks        : {self.Star_marks if hasattr(self, 'Star_marks') else 0}")
        print(f"Star Sacrificion stacks : {self.StarSacrificialValue if hasattr(self, 'StarSacrificialValue') else 0}")
    elif "Aria" in self.name:
        print(f"Elemental Shards    : {self.EleShard if hasattr(self, 'EleShard') else 0}")
        print(f"Elemental Crystals  : {self.EleCrystal if hasattr(self, 'EleCrystal') else 0}")
        print(f"Element Infusion    : {self.Element if hasattr(self, 'Element') else 'None'}")
    print(f"------------------------")
    print(f"Enemy HP :   {target.hp}/{target.max_hp} + {target.shield}")
    print(
        f"""target ATK:   {target.atk} + {(target.buffs.get("Attack Boost", {"value": 0})["value"] if "Attack Boost" in target.buffs else 0)}""")
    print(
        f"""target DEF:   {target.defense} + {(target.buffs.get("Defense Boost", {"value": 0})["value"] if "Defense Boost" in target.buffs else 0)}""")
    if "Arona" in target.name:
        print(f"Chronograph Value: {target.special_meter}/250")
    else:
        print(f"Current Charge: {target.special_meter}/(100)")


# Battle program
def Battle(Me, Enemy):
    while Me.hp > 0 or Enemy.hp > 0:
        Stats(Me, Enemy)
        SelfCurrentTurn(Me, Enemy, Me.special_meter)
        EnemyTurn(Enemy, Me, Enemy.special_meter)
        Me.post_turn(Enemy)
        Enemy.post_turn(Me)
        if Me.hp <= 0 and Enemy.hp <= 0:
            print(f"Both {Me.name} and {Enemy.name}'s HP reduced to 0.")
            print("it's a tie.")
            break
        elif Me.hp <= 0:
            print(f"{Me.name}'s HP reduced to 0.")
            print("You lost.")
            break
        elif Enemy.hp <= 0:
            print(f"{Enemy.name}'s HP reduced to 0.")
            print("You won.")
            break


# Character Select
def CharSelect():
    print("Select your character:")
    print("""1. Yuri
    HP : 600
    Base ATK : 70
    Base DEF : 10
    Special: Judgement Call
        Deals huge amount of damage equal to 3x/7x/13x of ATK as TRUE DAMAGE, and increase ATK by 20/40/70, CRIT RATE by
        30%/40%/60%, and CRIT DAMAGE by 50%/100%/200% for 3/4/5 turns. All DAMAGE dealt will be gained as HP.
    
    Passive: Executioner
        Gain 50% of your lost HP as ATK. 10% of DAMAGE dealt is also regained as HP.
""")
    print("""2. Akane
    HP : 500
    Base ATK : 10
    Base DEF : 50
    Special: Lethal Divination
    Removes all debuffs, heal yourself for 100/200/350 HP, and give yourself (30/60/100 + 10 * Revelation stacks) 
    DEF boost for 3 turns, and also inflict POISON to enemy for 3 turns.

    Passive: Invigoration
    Gain a stack of Revelation when dealing damage equal or less than (40 + Revelation * 10) DAMAGE to enemy.
    When gaining 10 stacks of Revelation, gain Reckoning.
    
    Revelation  : Gain 5 ATK for every stacks of Revelation in possession.
    Reckoning   : Increases Revelation's boost by 100% (including DEF boost) and enhances all attack to 
                  stun enemy for 2 turns by 75% chance.
    
    """)
    print("""3. Imakaze
        HP : 800
        Base ATK : 35
        Base DEF : 35
        Special: Iteration
            Divide your SPECIAL meter into 2 values, X and Y. X will heal you and increase your ATK based on the
            value count, while Y will deal TRUE damage to the enemy and increase your DEF based on the value count.
        
        Passive: Recognition
            Reduce SPECIAL charge efficiency by 30% and SPECIAL cap to 150, but SPECIAL can be triggered at 75
            Charge. When using SPECIAL, gain a stack of Integration, up to 3 stacks.
        
        Integration: Triggers your SPECIAL once more and charge your SPECIAL for 10 every stacks of Iteration currently held. 
        """)
    print("""4. Cosmos
        HP : 1000
        Base ATK : 30
        Base DEF : 40
        Special: The Stars are Aligning
            Consume all Stark Mark stats and Star Sacrificion stacks. if you have at least 8 Star Marks, inflict the enemy 
            with Guard Break, Armor Break, Cripple, Burn, Bleed, or Poison for 3 turns.
        Passive: Star Collapsing
            Every attack consumes either 8% of HP, ATK, or DEF, and gain 1 stack of "Star Mark." For every STATS POINTS
            consumed, gain 1 Star Sacrificion Stacks.
        
        Star Mark           : Each stack increases damage dealt by 8%. Upon using SPECIAL, gain extra 8% Star 
                              Sacrificion Stacks for every Star Mark stacks.
        Star Sacrificion    : A charge value for SPECIAL usage.
    """)

    print("""5. Aria 
        HP : 750
        Base ATK : 50
        Base DEF : 50
        Special: Elemental Wheel, Initiate!
            When using SPECIAL for the first time, infuse your weapon with an Elemental Variable. After using SPECIAL 
            for the first time, every time you trigger SPECIAL, heal for 50% of your MAX HP and switch your weapon infuse
            with another Elemental Variable. The buffs given by Elemental Variable is scaled through Elemental Crystals.
            When triggering SPECIAL, get an Elemental Crystal.
        Passive: The Calamity Remains
            When attacking using infused weapon, There's a chance to get 1, 2, or 3 Elemental Shards. When 7 Elemental
            Shards are collected, they fuse and become an Elemental Crystal. The chance of getting Elemental Shards 
            scales based on SPECIAL METER.
            
            First shard : Up to 75%
            Second shard: Up to 50%
            Third shard : Up to 25%
            
            Your SPECIAL METER charge efficiency decreases by 80%, and your SPECIAL METER is capped at 100. SPECIAL is
            usable within 50 charges.

        Elemental Variable: Buffs gained using special. The buffs are:
                    Pyro    : Increase ATK by (50 * Elemental Crystal)%. Attacks have (7 * Elemental Crystal)% chance
                              of inflicting BURN for 3 turns.
                    Hydro   : Continuously increase MAX HP by (10 + Elemental Crystal)%. Increases ATK by 
                              (50 * Elemental Crystal)% of MAX HP.
                    Cryo    : Increase CRIT RATE by (10 * Elemental Crystal)% and CRIT DAMAGE by (50 * Elemental Crystal)%.
                              Attacks have (7 * Elemental Crystal)% Chance to Freeze enemy for 3 turns. 
                              
                              Frozen: Unable to act, and decreases SPECIAL CHARGE efficiency by 100%.
                    Dendro  : Gain S-Thorns for the duration of this infusion. Attacks have (7 * Elemental Crystal)% chance
                              to trigger 2 more times.
                              S-Thorns: Reflect damage taken by (10 * Elemental Crystals)%
                    Electro : Increases DAMAGE by (50 * Elemental Crystal)%. Attacks have a chance to thunder down,
                              dealing (300 + 70 * Elemental Crystal)% of ATK and stunning them for 2 turns.
                    Geo     : Gain a shield equal to (50 + 10 * Elemental Crystal)% of MAX HP. Every turn, gain another
                              (10 + 2 * Elemental Crystal)% of MAX HP. While shielded, gain Quake.
                              
                              Quake: When attacking or getting attacked, deal TRUE DAMAGE equal to 90% of current shield.
                    Anemo   : Increase DEF by (50 * Elemental Crystal)%. Every turn, permanently increases MAX HP, ATK,
                              and DEF by (3 * Elemental Crystal).
    """)
    Select = int(input(">> "))
    if Select == 1:
        Me = Character("Yuri", 600, 70, 10, Yuri_super, Yuri_passive)
        return Me
    elif Select == 2:
        Me = Character("Akane", 500, 10, 50, Akane_super, Akane_passive)
        return Me
    elif Select == 3:
        Me = Character("Imakaze", 800, 35, 35, Imakaze_super, Imakaze_passive)
        return Me
    elif Select == 4:
        Me = Character("Cosmos", 1000, 30, 40, Cosmos_super, Cosmos_passive)
        return Me
    elif Select == 5:
        Me = Character("Aria", 750, 50, 50, Aria_super, Aria_passive)
        return Me


# Difficulty Select
def DiffSelect():
    while True:
        Start = 0
        print("Select Difficulty:")
        print("1. Easy")
        print("2. Normal")
        print("0. Exit")
        Diff = int(input(">> "))

        if Diff == 1:
            print("""
Difficulty: Easy
    HP  : 300-500
    ATK : 20-30
    DEF : 10-20
    
Specials in consideration:
    Backslash   : Increases own ATK by 3-5x the original ATK for 1 turn.
    Guard Ring  : Increases DEF by 50 for 2 turns, then heal self based on 50% up to 150% of current DEF value.
    En Garde    : Gain either Dead Eye or Precision for 3 turns. in return, target gains 20 extra DEF for 2 turns.""")
            HP = int(random.randrange(350, 500, 50))
            ATK = int(random.randrange(20, 30, 2))
            DEF = int(random.randrange(10, 20, 2))
            EnemyNum = random.randint(1, 3)
            if EnemyNum == 1:
                Enemy = Character("Aoi", HP, ATK, DEF, Super_E1, None)
            elif EnemyNum == 2:
                Enemy = Character("Nana", HP, ATK, DEF, Super_E2, None)
            elif EnemyNum == 3:
                Enemy = Character("Bili", HP, ATK, DEF, Super_E3, None)
            return Enemy, True

        elif Diff == 2:
            print("""
Yes, I'm amping everything up. Fk you.            

Difficulty: Normal
    HP  : 800-1000
    ATK : 35-50
    DEF : 20-35

Specials in consideration:
    Quantum Cascade:
        Deal 2 instances of damage as TRUE DAMAGE. each attack has a 50% chance to trigger Quantum Fissure, "splitting"
        the attacks and dealing 2 more instances of damage. Up to 10 damage count can be triggered this way. When dealing
        5 or more instances of damage, inflict Entanglement to the target for 3 turns.
        
        Entanglement: Reduces damage by 60%. Attacks has 60% chance to trigger again.
        
    Solar Implosion:
        Heal yourself for 70% HP lost between SPECIAL triggers and deal TRUE DAMAGE equal to 30% of your healing to the
        enemy. For every SPECIAL trigger, increase the damage treshold by 10%. Up to 200% of heal can be converted this way.
        When your HP is below 30%, Enter the Solar Flare state.
        
        Passive: Solar Flare
            All SPECIAL trigger counts will be inherited to Solar Flare. While in Solar Flare, inflict enemy
            with Burn. When triggering SPECIAL, gain a shield equal to (10 * SPECIAL trigger count). SPECIAL
            CHARGE efficiency while in Solar Flare is increased by 250%.
                     
    Dimensional Rift:
        Deal an instance of damage equal to 150% of ATK and leave 3 Rift marks. Rift explosions damage dealt this way
        is increased by 20% for each Rift marks exploded.
        
        Passive: Space-Time In My Hand... Kinda.
            Attacks have a 39% chance to leave a Rift Mark. When 3 or more Rift Marks exist simultaneously, All Rift
            Marks will explode, each dealing 70% of ATK as TRUE DAMAGE to enemy. When 5 or more Rift marks explode 
            simultaneously, all damage given will also received by you.
        """)

            HP = int(random.randrange(800, 1000, 40))
            ATK = int(random.randrange(35, 50, 3))
            DEF = int(random.randrange(20, 35, 3))
            EnemyNum = random.randint(1, 3)
            EnemyNum = 2
            if EnemyNum == 1:
                Enemy = Character("Rikan", HP, ATK, DEF, Super_N1, None)
            elif EnemyNum == 2:
                Enemy = Character("Kaede", HP, ATK, DEF, Super_N2, Passive_N2)
            elif EnemyNum == 3:
                Enemy = Character("Lily", HP, ATK, DEF, Super_N3, Passive_N3)
            return Enemy, True

        elif Diff == 3:
            print("""
Mr Stark? I don't feel so good...            

Difficulty: Hard
    HP  : 1200-1500
    
    ATK : 55-70
    DEF : 40-50

Specials in consideration:
    Blood Deal:
        Heal for 100 HP and gain a Soul mark.
        
        Passive: Sacrificion Trademark
            When HP is below 500, Consume all Soul marks and inflict DOOM to enemy at an initial of 20 turns. Every Soul
            marks consumed will reduce the turns by 1 and give 30 DEF. Special will be unusable in this state.
    
    Cycle of life:
        SPECIAL METER now acts as Chronograph. When Chronograph is full, switch state between Everday and Nightfall.
        Reminiscing In The Sunlight:
            Enters the Everday state. Upon entering the Everday state, heal yourself by 10% of MAX HP.
            While in the Everday state, increase ATK and DEF by 75%, CRIT RATE by 50%, CRIT DAMAGE
            by 100%, and attacks have a 50% chance to heal yourself by 50% of damage dealt. 

        Bathing In The Moonlight:
            Enters the Nightfall state. Upon entering the Nightfall state, increase MAX HP by 100%. 
            While in the Nightfall state, for every 5% of MAX HP lost, gain a stack of Twilight.
            
            Everday and Nightfall state has 250 Chronograph Points.
            
            Twilight: Increase damage taken by 10% and damage dealt by 10%. 
    
    Ghost House:
        Summons a Spirit, up to 5 Spirits.
        
        Passive: Undead Initiated
            When taking fatal damage, immediately heals for 1000 HP consume all Spirits currently exist. For every 
            Spirit consumed increase ATK by 15, DEF by 15, and Shield by 200. Every turn, lose 50 HP, 5 ATK,
            and 5 DEF, down to 1.
        
        
        Spirit:
            Every Spirit increases ATK and DEF by 5. When 5 Spirits exist, inflict POISON to Enemy. When taking damage 
            equal to or higher than 100, a spirit explodes, dealing 50-100 TRUE DAMAGE and inflicting CRIPPLE for 2 turns.
        
    Moonstruck:
        Gain 500 Shield. If Moon Glow is active, convert all excess shield into Attack and Defense and reset your
        shield back to 500. 
        
        Passive: Moon Glow
        While shield is active, gain Moon Glow effect.
        
        Moon Glow:
            While Moon Glow is active, increase all damage by 50%, and all damage becomes True Damage.
            
        """)

            HP = int(random.randrange(1200, 1500, 50))
            ATK = int(random.randrange(55, 70, 3))
            DEF = int(random.randrange(40, 50, 2))
            EnemyNum = random.randint(1, 3)
            EnemyNum = 4
            if EnemyNum == 1:
                Enemy = Character("Lilith", HP, ATK, DEF, Super_H1, Passive_H1)
            elif EnemyNum == 2:
                Enemy = Character("Arona", HP, ATK, DEF, Super_H2, Passive_H2)
            elif EnemyNum == 3:
                Enemy = Character("Lily", HP, ATK, DEF, Super_H3, Passive_H3)
            elif EnemyNum == 4:
                Enemy = Character("Chang'e", HP, ATK, DEF, Super_H4, Passive_H4)
            return Enemy, True

        elif Diff == 4:
            print("""
HHWHWHEHWEHWEHWEHWEHWEHWEHWEHEWH

Difficulty: Insane
    HP  : 2000-2500

    ATK : 70-90
    DEF : 55-70

Specials in consideration:
    Unflinching:
        Gain 20-30 stacks of Pride and deal True Damage equal to 10 * Pride stacks gained on this Special. 
        
        Passive: Unbreaking
            At the start of the battle, gain 30 stacks of Pride. Every turn, convert 5-10 stacks of Pride into Rage.
            Up to 150 Rage can be gained this way. When Rage reaches 100 stacks, gain Strike.  
            
        Pride: Each stack of Pride increases DEF by 1.
        Rage: Each stack of Rage increases ATK by 1.
        Strike: Upon gaining Strike, each stack of Rage also increases DMG by 1%.
""")

            HP = int(random.randrange(2000, 2500, 50))
            ATK = int(random.randrange(70, 90, 5))
            DEF = int(random.randrange(55, 70, 3))
            EnemyNum = random.randint(1, 4)
            EnemyNum = 1
            if EnemyNum == 1:
                Enemy = Character("Franz", HP, ATK, DEF, Super_I1, Passive_I1)
            elif EnemyNum == 2:
                Enemy = Character("Arona", HP, ATK, DEF, Super_H2, Passive_H2)
            elif EnemyNum == 3:
                Enemy = Character("Lily", HP, ATK, DEF, Super_H3, Passive_H3)
            elif EnemyNum == 4:
                Enemy = Character("Chang'e", HP, ATK, DEF, Super_H4, Passive_H4)
            return Enemy, True


# Main program
while True:
    print("Welcome to my game, with a whole new refined stuffs.")
    print("1. Battle")
    print("2. How to play")
    print("3. Exit")
    SelectMenu = int(input(">> "))

    if SelectMenu == 1:
        while True:
            print("Welcome to my game, with a whole new refined stuffs.")
            print("1. Regular Battle")
            print("2. Tower of Ridila")
            print("3. Back")
            SelectBattle = int(input(">> "))
            if SelectBattle == 1:
                Me = CharSelect()
                while True:
                    Enemy, DiffStart = DiffSelect()
                    print("Are you sure?")
                    Sure = input("(Y/N) >> ")
                    if Sure == "Y":
                        break
                    else:
                        pass
                Battle(Me, Enemy)
                break
            elif SelectBattle == 2:
                print("Nuh uh, not yet")
            elif SelectBattle == 3:
                break
    elif SelectMenu == 3:
        print("Goodbye :D")
        break
