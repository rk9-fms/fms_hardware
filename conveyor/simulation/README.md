# Conveyor simulation

Simulates physical conveyor

### How to

Just start the `visualiser.py`

### Structure

Core of simulation is a `conveyor.simulation.simulation.Conveyor`.
This a time-based simulation.

Listener is based on socketserver

Visualiser is based on tkinter

```
# in this case works both with listener and conveyor simulation, 
# because visualiser based on tkinter visualising them both
conveyor.simulation.visualizer.TkVisualiser
                     < - >  
+--------------------------------------------------+
|# listener for interprocess communication         |
|conveyor.simulation.listener.SocketServerListener |
|                    < - >                         |
|# simulation core                                 |
|conveyor.simulation.simulation.Conveyor           |
+--------------------------------------------------+
``` 
