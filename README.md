Final project for Music 128 Topics in Music History: Music and Data. Visualization and sonification of global glacier region mass balance.

[GitHub repository](https://github.com/ethzhou/sonification-glaciers/). Python 3.12.8.

## Run

Open the directory in terminal, and enter

```
chmod +x sonification.sh
```

to make the file executable. Then, run the program by entering

```
./sonification.sh
```

## Packages

- Pygame==2.6.1
- numpy==1.26.4

## Controls

- MOUSEWHEEL
  - change cursor radius
- DOWNARROW
  - cycle statistic
    - This toggles the measure of mass balance between units of meters of water equivalent and gigatons.
- N
  - jump to next year
