from abc import ABC, abstractmethod
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, Future
import threading
import time

class Bird(ABC):
    def __init__(self, species: str, habitat: str, wing_span: float, weight: float, max_altitude: int, is_migratory: bool):
        self._species = species
        self._habitat = habitat
        self._wing_span = wing_span
        self._weight = weight
        self._max_altitude = max_altitude
        self._is_migratory = is_migratory
    
    @abstractmethod
    def perform_flight(self, plan: 'FlightPlan') -> 'FlightResult':
        pass
    
    @abstractmethod
    def get_max_flight_speed(self) -> float:
        pass
    
    @abstractmethod
    def get_flight_efficiency(self) -> float:
        pass
    
    @abstractmethod
    def get_max_flight_duration(self) -> int:
        pass
    
    @abstractmethod
    def can_fly_at_altitude(self, altitude: int) -> bool:
        pass
    
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

class Albatross(Bird):
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

class Falcon(Bird):
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

class Emperor(Bird):
    def __init__(self):
        super().__init__("Emperor Penguin", "Antarctica", 0.8, 30.0, 0, False)
        self._swim_speed = 15.0
    
    def perform_flight(self, plan: FlightPlan) -> FlightResult:
        raise NotImplementedError("Emperor penguins are flightless! They can only swim and walk.")
    
    def get_max_flight_speed(self) -> float:
        return 0.0
    
    def get_flight_efficiency(self) -> float:
        return 0.0
    
    def get_max_flight_duration(self) -> int:
        return 0
    
    def can_fly_at_altitude(self, altitude: int) -> bool:
        return False
    
    @property
    def swim_speed(self) -> float:
        return self._swim_speed
    
    def swim(self, distance: float) -> str:
        time_hours = distance / self._swim_speed
        return f"Swimming {distance:.2f} km in {time_hours:.2f} hours"

class AdvancedFlightManager:
    def __init__(self):
        self._flock: List[Bird] = []
        self._flight_executor = ThreadPoolExecutor(max_workers=10)
    
    def add_bird(self, bird: Bird) -> None:
        self._flock.append(bird)
    
    def execute_formation_flight(self, plan: FlightPlan) -> None:
        print("=== Formation Flight Execution ===")
        print(f"Flight Plan: {plan.distance}km at {plan.altitude}m altitude")
        
        futures: List[Future[FlightResult]] = []
        
        for bird in self._flock:
            future = self._flight_executor.submit(self._execute_bird_flight, bird, plan)
            futures.append(future)
        
        for i, future in enumerate(futures):
            try:
                result = future.result()
                bird = self._flock[i]
                print(f"{bird.species}: {result.status}")
                if result.successful:
                    print(f"  Distance: {result.actual_distance}km, Duration: {result.actual_duration}min")
            except Exception as e:
                print(f"{self._flock[i].species}: Flight failed - {str(e)}")
            print("---")
    
    def _execute_bird_flight(self, bird: Bird, plan: FlightPlan) -> FlightResult:
        print(f"Starting flight for {bird.species}")
        return bird.perform_flight(plan)
    
    def perform_flight_capability_analysis(self) -> None:
        print("=== Flight Capability Analysis ===")
        for bird in self._flock:
            print(f"{bird.species}:")
            print(f"  Max Speed: {bird.get_max_flight_speed()} km/h")
            print(f"  Efficiency: {bird.get_flight_efficiency()}")
            print(f"  Max Duration: {bird.get_max_flight_duration()} minutes")
            print(f"  Max Altitude: {bird.max_altitude}m")
            print()
    
    def shutdown(self) -> None:
        self._flight_executor.shutdown()