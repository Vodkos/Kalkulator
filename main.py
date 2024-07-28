import streamlit as st
import numpy as np

# Constants for the calculations
AVERAGE_SOLAR_IRRADIANCE = 1000  # kWh per kWp per year, this can vary based on location
BATTERY_EFFICIENCY = 0.9

# Define self-consumption matrix
self_consumption_matrix = {
    6.2: {
        2000: {3: 0.60, 6: 0.50, 9: 0.40, 12: 0.35, 15: 0.30, 20: 0.25},
        4000: {3: 0.55, 6: 0.50, 9: 0.45, 12: 0.40, 15: 0.35, 20: 0.30},
        6000: {3: 0.50, 6: 0.50, 9: 0.45, 12: 0.40, 15: 0.35, 20: 0.30},
        8000: {3: 0.45, 6: 0.40, 9: 0.35, 12: 0.30, 15: 0.25, 20: 0.20},
        10000: {3: 0.40, 6: 0.35, 9: 0.30, 12: 0.25, 15: 0.20, 20: 0.15}
    },
    9.3: {
        2000: {3: 0.65, 6: 0.55, 9: 0.50, 12: 0.45, 15: 0.40, 20: 0.35},
        4000: {3: 0.60, 6: 0.55, 9: 0.50, 12: 0.45, 15: 0.40, 20: 0.35},
        6000: {3: 0.55, 6: 0.50, 9: 0.45, 12: 0.40, 15: 0.35, 20: 0.30},
        8000: {3: 0.50, 6: 0.45, 9: 0.40, 12: 0.35, 15: 0.30, 20: 0.25},
        10000: {3: 0.45, 6: 0.40, 9: 0.35, 12: 0.30, 15: 0.25, 20: 0.20}
    },
    12.4: {
        2000: {3: 0.70, 6: 0.60, 9: 0.55, 12: 0.50, 15: 0.45, 20: 0.40},
        4000: {3: 0.65, 6: 0.60, 9: 0.55, 12: 0.50, 15: 0.45, 20: 0.40},
        6000: {3: 0.60, 6: 0.55, 9: 0.50, 12: 0.45, 15: 0.40, 20: 0.35},
        8000: {3: 0.55, 6: 0.50, 9: 0.45, 12: 0.40, 15: 0.35, 20: 0.30},
        10000: {3: 0.50, 6: 0.45, 9: 0.40, 12: 0.35, 15: 0.30, 20: 0.25}
    }
}

def get_self_consumption_fraction(pv_size, battery_capacity, annual_energy_consumption):
    if battery_capacity in self_consumption_matrix:
        capacity_matrix = self_consumption_matrix[battery_capacity]
        closest_consumption = min(capacity_matrix.keys(), key=lambda x: abs(x - annual_energy_consumption))
        closest_pv_size = min(capacity_matrix[closest_consumption].keys(), key=lambda x: abs(x - pv_size))
        return capacity_matrix[closest_consumption][closest_pv_size]
    else:
        return 0.2  # Default value if no match found

# Functions for calculations
def calculate_annual_production(pv_size):
    return pv_size * AVERAGE_SOLAR_IRRADIANCE

def calculate_self_consumption(pv_size, battery_capacity, annual_energy_consumption):
    self_consumption_fraction = get_self_consumption_fraction(pv_size, battery_capacity, annual_energy_consumption)
    production = calculate_annual_production(pv_size)
    self_consumed = min(production * self_consumption_fraction, annual_energy_consumption)
    return self_consumed

def calculate_grid_feed(production, self_consumed):
    return max(production - self_consumed, 0)

def calculate_grid_energy_usage(annual_energy_consumption, self_consumed):
    return max(annual_energy_consumption - self_consumed, 0)

def calculate_savings(self_consumed_energy, grid_feed_energy, grid_energy_usage, purchase_price, sell_price):
    savings_from_self_consumption = self_consumed_energy * purchase_price
    earnings_from_grid_feed = grid_feed_energy * sell_price
    cost_of_grid_usage = grid_energy_usage * purchase_price
    return savings_from_self_consumption + earnings_from_grid_feed - cost_of_grid_usage

def find_optimal_pv_size(annual_energy_consumption, battery_capacity, pv_sizes, purchase_price, sell_price):
    optimal_pv_size = None
    max_savings = -float('inf')

    for pv_size in pv_sizes:
        production = calculate_annual_production(pv_size)
        self_consumed_energy = calculate_self_consumption(pv_size, battery_capacity, annual_energy_consumption)

        if self_consumed_energy is None:
            continue

        grid_feed_energy = calculate_grid_feed(production, self_consumed_energy)
        grid_energy_usage = calculate_grid_energy_usage(annual_energy_consumption, self_consumed_energy)

        savings = calculate_savings(self_consumed_energy, grid_feed_energy, grid_energy_usage, purchase_price, sell_price)

        if savings > max_savings:
            max_savings = savings
            optimal_pv_size = pv_size
            optimal_production = production
            optimal_self_consumed_energy = self_consumed_energy
            optimal_grid_feed_energy = grid_feed_energy
            optimal_grid_energy_usage = grid_energy_usage

    return optimal_pv_size, max_savings, optimal_production, optimal_self_consumed_energy, optimal_grid_feed_energy, optimal_grid_energy_usage

def calculate_cost(annual_energy_consumption, purchase_price):
    return annual_energy_consumption * purchase_price

# Streamlit app
st.title("Kalkulator Oszczędności z Instalacji PV")

annual_energy_consumption = st.number_input("Roczne zużycie energii (kWh)", value=4000)
battery_capacity = st.selectbox("Pojemność magazynu energii (kWh)", [6.2, 9.3, 12.4])
purchase_price = st.number_input("Cena zakupu energii (zł/kWh)", value=1.20)
sell_price = st.number_input("Cena sprzedaży energii (zł/kWh)", value=0.40)

if st.button("Oblicz"):
    annual_cost = calculate_cost(annual_energy_consumption, purchase_price)

    # PV sizes in 0.4 kWp intervals from 3 to 20 kWp
    pv_sizes = [i * 0.4 for i in range(8, 51)]

    optimal_pv_size, max_savings, production, self_consumed_energy, grid_feed_energy, grid_energy_usage = find_optimal_pv_size(
        annual_energy_consumption, battery_capacity, pv_sizes, purchase_price, sell_price
    )

    if optimal_pv_size is not None:
        # Display results
        st.write("### Wyniki Obliczeń")
        st.write(f"**Roczny koszt zużycia energii:** {annual_cost:.2f} zł")
        st.write(f"**Sugerowana moc instalacji PV:** {optimal_pv_size:.1f} kWp")
        st.write(f"**Autokonsumpcja:** {self_consumed_energy:.2f} kWh ({self_consumed_energy * purchase_price:.2f} zł)")
        st.write(f"**Ilość energii oddanej do sieci:** {grid_feed_energy:.2f} kWh ({grid_feed_energy * sell_price:.2f} zł)")
        st.write(f"**Ilość energii pobranej z sieci:** {grid_energy_usage:.2f} kWh ({grid_energy_usage * purchase_price:.2f} zł)")
        st.write(f"**Oszczędności roczne:** {max_savings:.2f} zł")
    else:
        st.write("Brak danych dla podanego rocznego zużycia energii i pojemności magazynu.")
