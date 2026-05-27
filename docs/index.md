# PLUTOpython

A PLUTO ([ECSS-E-ST-70-32C](https://ecss.nl/standard/ecss-e-st-70-32c-space-engineering-test-and-operations-procedure-language/)) to Python transpiler and runtime.

Take a spacecraft operations procedure written in PLUTO and get back a runnable Python program.

```pluto
procedure
    declare
      event chaos described by Total disaster
    end declare
    main
      initiate Switch on Star Tracker2
      in parallel until all complete
        initiate and confirm step BRING UP REACTION WHEEL
          main
            initiate and confirm Switch on Reaction Wheel3 of AOC of Satellite;
          end main
        end step;
        initiate and confirm step BRING UP STAR TRACKER
          main
            initiate and confirm Switch on Star Tracker1;
          end main
        end step;
      end parallel
    end main
end procedure
```

```bash
$ pip install plutopy
$ plutopy run script.pluto
[ACTIVITY] Switch on Star Tracker2
[ACTIVITY] Switch on Reaction Wheel3 of AOC of Satellite
[ACTIVITY] Switch on Star Tracker1
```

## Highlights

- **Real transpiler, not a tree-walker.** PLUTO → readable Python source that imports a small runtime library.
- **Live TUI demo.** `plutopy demo` visualises a fake satellite reacting to your procedure in real time.
- **Friendly errors.** Parse failures show source line, column, and a caret with a structural hint.
- **Modern Python packaging.** `pip install plutopy`, console script, GitHub Actions matrix on 3.9 / 3.11 / 3.13.
- **Pygments syntax highlighter.** `pygmentize -l pluto …` (and these very docs use it).

## Continue reading

- [Playground](playground/index.html) — write PLUTO and run it in your browser, no install
- [Quickstart](quickstart.md) — install, run, write your first PLUTO procedure
- [Grammar reference](grammar.md) — every supported PLUTO construct
- [Examples](examples.md) — five demos exercising the language
- [Architecture](architecture.md) — how the pipeline fits together
- [Finish-Up-A-Thon arc](arc.md) — what was here in 2019, what's here now
