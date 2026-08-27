from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from concurrent.futures import ThreadPoolExecutor, Future
import threading
import time

class Flyable(Protocol):
    def perform_flight(self, plan: 'FlightPlan') -> 'FlightResult':
        pass
    
    def get_max_flight_speed(self) -> float:
        pass
    
    def get_flight_efficiency(self) -> float:
        pass
    
    def get_max_flight_duration(self) -> int:
        pass
    
    def can_fly_at_altitude(self, altitude: int) -> bool:
        pass

class Swimmable(Protocol):
    def swim(self, distance: float) -> str:
        pass
    
    @property
    def swim_speed(self) -> float:
        pass

class Animal(ABC):
    def __init__(self, species: str, habitat: str, wing_span: float, weight: float, max_altitude: int, is_migratory: bool):
        self._species = species
        self._habitat = habitat
        self._wing_span = wing_span
        self._weight = weight
        self._max_altitude = max_altitude
        self._is_migratory = is_migratory
    
    @property
    def species(self) -> str:
        return self._species
    
    @property
    def habitat(self) -> str:
        return self._habitat
    
    @property
    def wing_span(self) -> float:
        return self._wing_span
    
    @property
    def weight(self) -> float:
        return self._weight
    
    @property
    def max_altitude(self) -> int:
        return self._max_altitude
    
    @property
    def is_migratory(self) -> bool:
        return self._is_migratory

class FlightPlan:
    def __init__(self, distance: float, altitude: int, direction: str, planned_duration: int):
        self._distance = distance
        self._altitude = altitude
        self._direction = direction
        self._planned_duration = planned_duration
    
    @property
    def distance(self) -> float:
        return self._distance
    
    @property
    def altitude(self) -> int:
        return self._altitude
    
    @property
    def direction(self) -> str:
        return self._direction
    
    @property
    def planned_duration(self) -> int:
        return self._planned_duration

class FlightResult:
    def __init__(self, successful: bool, actual_distance: float, actual_duration: int, status: str):
        self._successful = successful
        self._actual_distance = actual_distance
        self._actual_duration = actual_duration
        self._status = status
    
    @property
    def successful(self) -> bool:
        return self._successful
    
    @property
    def actual_distance(self) -> float:
        return self._actual_distance
    
    @property
    def actual_duration(self) -> int:
        return self._actual_duration
    
    @property
    def status(self) -> str:
        return self._status

class Albatross(Animal, Flyable):
    def __init__(self):
        super().__init__("Wandering Albatross", "Ocean", 3.5, 8.5, 15000, True)
    
    def perform_flight(self, plan: FlightPlan) -> FlightResult:
        if not self.can_fly_at_altitude(plan.altitude):
            return FlightResult(False, 0, 0, "Altitude too high for sustained flight")
        
        efficiency = self.get_flight_efficiency()
        actual_distance = plan.distance * efficiency
        actual_duration = int(plan.planned_duration / efficiency)
        
        return FlightResult(True, actual_distance, actual_duration, "Long-distance flight completed successfully")
    
    def get_max_flight_speed(self) -> float:
        return 120.0
    
    def get_flight_efficiency(self) -> float:
        return 1.2
    
    def get_max_flight_duration(self) -> int:
        return 1440
    
    def can_fly_at_altitude(self, altitude: int) -> bool:
        return altitude <= self.max_altitude

class Falcon(Animal, Flyable):
    def __init__(self):
        super().__init__("Peregrine Falcon", "Cliffs", 1.2, 1.5, 20000, False)
    
    def perform_flight(self, plan: FlightPlan) -> FlightResult:
        if not self.can_fly_at_altitude(plan.altitude):
            return FlightResult(False, 0, 0, "Altitude exceeds maximum capability")
        
        speed = self.get_max_flight_speed()
        actual_distance = min(plan.distance, speed * (plan.planned_duration / 60.0))
        actual_duration = int(actual_distance / speed * 60)
        
        return FlightResult(True, actual_distance, actual_duration, "High-speed flight completed")
    
    def get_max_flight_speed(self) -> float:
        return 300.0
    
    def get_flight_efficiency(self) -> float:
        return 0.8
    
    def get_max_flight_duration(self) -> int:
        return 180
    
    def can_fly_at_altitude(self, altitude: int) -> bool:
        return altitude <= self.max_altitude

class Emperor(Animal, Swimmable):
    def __init__(self):
        super().__init__("Emperor Penguin", "Antarctica", 0.8, 30.0, 0, False)
        self._swim_speed = 15.0
    
    @property
    def swim_speed(self) -> float:
        return self._swim_speed
    
    def swim(self, distance: float) -> str:
        time_hours = distance / self._swim_speed
        return f"Swimming {distance:.2f} km in {time_hours:.2f} hours"

class FlightCapable:
    def __init__(self, flyable: Flyable):
        self._flyable = flyable
    
    def execute_flight(self, plan: FlightPlan) -> FlightResult:
        return self._flyable.perform_flight(plan)
    
    def get_capabilities(self) -> dict:
        return {
            'max_speed': self._flyable.get_max_flight_speed(),
            'efficiency': self._flyable.get_flight_efficiency(),
            'max_duration': self._flyable.get_max_flight_duration()
        }

class SwimCapable:
    def __init__(self, swimmable: Swimmable):
        self._swimmable = swimmable
    
    def execute_swim(self, distance: float) -> str:
        return self._swimmable.swim(distance)
    
    def get_swim_speed(self) -> float:
        return self._swimmable.swim_speed

class AdvancedFlightManager:
    def __init__(self):
        self._flight_capable: List[FlightCapable] = []
        self._swim_capable: List[SwimCapable] = []
        self._flight_executor = ThreadPoolExecutor(max_workers=10)
    
    def add_flyable(self, flyable: Flyable) -> None:
        self._flight_capable.append(FlightCapable(flyable))
    
    def add_swimmable(self, swimmable: Swimmable) -> None:
        self._swim_capable.append(SwimCapable(swimmable))
    
    def execute_formation_flight(self, plan: FlightPlan) -> None:
        print("=== Formation Flight Execution ===")
        print(f"Flight Plan: {plan.distance}km at {plan.altitude}m altitude")
        
        futures: List[Future[FlightResult]] = []
        
        for flight_capable in self._flight_capable:
            future = self._flight_executor.submit(self._execute_flight, flight_capable, plan)
            futures.append(future)
        
        for i, future in enumerate(futures):
            try:
                result = future.result()
                print(f"Aircraft {i+1}: {result.status}")
                if result.successful:
                    print(f"  Distance: {result.actual_distance}km, Duration: {result.actual_duration}min")
            except Exception as e:
                print(f"Aircraft {i+1}: Flight failed - {str(e)}")
            print("---")
    
    def _execute_flight(self, flight_capable: FlightCapable, plan: FlightPlan) -> FlightResult:
        print(f"Starting flight")
        return flight_capable.execute_flight(plan)
    
    def perform_flight_capability_analysis(self) -> None:
        print("=== Flight Capability Analysis ===")
        for i, flight_capable in enumerate(self._flight_capable):
            capabilities = flight_capable.get_capabilities()
            print(f"Aircraft {i+1}:")
            print(f"  Max Speed: {capabilities['max_speed']} km/h")
            print(f"  Efficiency: {capabilities['efficiency']}")
            print(f"  Max Duration: {capabilities['max_duration']} minutes")
            print()
    
    def shutdown(self) -> None:
        self._flight_executor.shutdown()