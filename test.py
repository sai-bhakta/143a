import os
import subprocess
import sys
from pathlib import Path

def run_test(simulation_file):
    simulation_path = f"simulator/simulations/{simulation_file}"
    correct_output_path = f"simulator/correct_output/{simulation_file}".replace(".json", ".txt")
    
    cmd = ["python3", "simulator/simulator.py", simulation_path, "output.txt"]
    subprocess.run(cmd)
    
    with open("output.txt", 'r') as f, open(correct_output_path, 'r') as f2:
        generated = f.readlines()
        correct = f2.readlines()
    
    passed = len(generated) == len(correct)
    for i in range(min(len(generated), len(correct))):
        if generated[i] != correct[i]:
            print(f"Line {i+1}:")
            print(f"Generated: {generated[i].strip()}")
            print(f"Correct:   {correct[i].strip()}")
            passed = False
    return passed

def main():
    simulations_dir = "simulator/simulations"
    simulation_files = [f for f in os.listdir(simulations_dir)]    
    
    for simulation_file in simulation_files:
        print(f"\nTesting {simulation_file}...")
        passed = run_test(simulation_file)
        print('PASSED' if passed else 'FAILED')

if __name__ == "__main__":
    sys.exit(main())