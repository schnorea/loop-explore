# Loop Bounds Analysis Report

## Overview
- **Total Loops**: 7,824
- **Loops with Bounds**: 7,824
- **Coverage**: 100.0%

## Initialization Patterns (Top 20)
- `Loop = 1`: 438 loops
- `i = 1`: 401 loops
- `SurfNum = 1`: 153 loops
- `I = 1`: 147 loops
- `SetPtMgrNum = 1`: 146 loops
- `j = 1`: 136 loops
- `Item = 1`: 112 loops
- `ZoneNum = 1`: 110 loops
- `CompNum = 1`: 93 loops
- `NodeNum = 1`: 86 loops
- `BranchNum = 1`: 83 loops
- `Count = 1`: 65 loops
- `CtrlNodeIndex = 1`: 61 loops
- `Loop1 = 1`: 57 loops
- `k = 1`: 55 loops
- `int i = 1;`: 51 loops
- `J = 1`: 49 loops
- `loop = 1`: 48 loops
- `IGlass = 1`: 48 loops

## Condition Patterns (Top 20)
- `SurfNum <= TotSurfaces`: 115 loops
- `ZoneNum <= NumOfZones`: 105 loops
- `true`: 53 loops
- `Loop1 <= NumValidIntConvectionValueTypes`: 47 loops
- `AirLoopNum <= NumPrimaryAirSys`: 43 loops
- `i <= nlayer`: 41 loops
- `CtrlZone <= NumOfZones`: 41 loops
- `iZone <= NumOfZones`: 40 loops
- `vert <= Surface( surf ).Sides`: 38 loops
- `CtrlZoneNum <= NumOfZones`: 37 loops
- `ControlledZoneNum <= NumOfZones`: 34 loops
- `SurfNum <= Zone( ZoneNum ).SurfaceLast`: 33 loops
- `LoopNum <= TotNumLoops`: 33 loops
- `pos != std::string::npos`: 30 loops
- `I <= NL`: 29 loops
- `TS <= NumOfTimeStepInHour`: 28 loops
- `StackDepth <= ConvergLogStackDepth`: 28 loops
- `i <= AirflowNetworkNumOfNodes`: 27 loops
- `i <= NumFMUObjects`: 27 loops
- `CtrldNodeNum <= NumNodesCtrld`: 26 loops

## Increment Patterns (Top 20)
- `++i`: 590 loops
- `++Loop`: 466 loops
- `++SurfNum`: 220 loops
- `++I`: 180 loops
- `++j`: 171 loops
- `++SetPtMgrNum`: 146 loops
- `++ZoneNum`: 114 loops
- `++Item`: 113 loops
- `++Loop1`: 110 loops
- `++CompNum`: 101 loops
- `++NodeNum`: 99 loops
- `++BranchNum`: 90 loops
- `++Count`: 73 loops
- `++J`: 61 loops
- `++CtrlNodeIndex`: 61 loops
- `++k`: 59 loops
- `++loop`: 56 loops
- `++n`: 53 loops
- `++Ctd`: 51 loops

## Variable Name Analysis
- **i**: 657 loops
- **Loop**: 473 loops
- **SurfNum**: 225 loops
- **j**: 199 loops
- **I**: 196 loops
- **SetPtMgrNum**: 146 loops
- **ZoneNum**: 120 loops
- **Item**: 113 loops
- **Loop1**: 110 loops
- **CompNum**: 104 loops
- **NodeNum**: 101 loops
- **BranchNum**: 91 loops
- **Count**: 73 loops
- **k**: 73 loops
- **J**: 66 loops

## Comparison Operators
- **<=**: 7345 loops
- **<**: 127 loops
- **>=**: 110 loops
- **>**: 52 loops
- **!=**: 60 loops
- **==**: 15 loops

## Increment Types
- **pre/post_increment**: 7325 loops
- **other**: 363 loops
- **pre/post_decrement**: 106 loops
- **compound_addition**: 28 loops
- **compound_subtraction**: 2 loops

## Iteration Estimates
- **unknown**: 7824 loops
