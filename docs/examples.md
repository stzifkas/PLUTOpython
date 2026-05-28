# Examples

All examples live in the [`examples/`](https://github.com/stzifkas/pluto-ecss/tree/main/examples) directory and ship as part of the repository.

## 1. The original GSoC demo

The 2019 script, untouched. Switches on a star tracker, then in parallel brings up another tracker and a reaction wheel.

```pluto
procedure
    declare
      event chaos described by Total disaster, event chaos2
    end declare
    main
      initiate Switch on Star Tracker2
      in parallel until all complete
        initiate and confirm step SWITCH ON SECOND STAR TRACKER
          main
            initiate and confirm Switch on Reaction Wheel3 of AOC of Satellite;
          end main
        end step;
        initiate and confirm step SWITCH ON FIRST STAR TRACKER
          main
            initiate and confirm Switch on Star Tracker1;
          end main
        end step;
      end parallel
    end main
end procedure
```

```text
$ pluto-ecss run examples/01_original.pluto
[ACTIVITY] Switch on Star Tracker2
[ACTIVITY] Switch on Reaction Wheel3 of AOC of Satellite
[ACTIVITY] Switch on Star Tracker1
```

## 2. Assignment, comparison, conditional

```pluto
procedure
    main
      threshold := 42
      observed := 40
      log "before observation"
      inform user "threshold set to 42"
      if observed < threshold then
        log "below threshold"
        inform user "all clear"
      end if
    end main
end procedure
```

## 3. Loops

```pluto
procedure
    main
      counter := 0
      while counter < 3 do
        log "loop iteration"
        counter := counter + 1
      end while
      for i := 1 to 3 do
        log "for iteration"
      end for
      inform user "loops finished"
    end main
end procedure
```

## 4. Events

```pluto
procedure
    declare
      event ready described by System bring up complete
    end declare
    main
      log "raising ready"
      raise event ready
      wait for event ready
      log "ready observed; continuing"
      initiate and confirm Switch on Star Tracker1
    end main
end procedure
```

## 5. Full bring-up (loops + parallel + events)

```pluto
procedure
    declare
      event boom described by Critical failure
    end declare
    main
      retries := 0
      while retries < 2 do
        log "attempting bring up"
        in parallel until all complete
          initiate and confirm step BRING UP REACTION WHEEL
            main
              initiate and confirm Switch on Reaction Wheel3 of AOC of Satellite;
            end main
          end step;
          initiate and confirm step BRING UP STAR TRACKERS
            main
              initiate and confirm Switch on Star Tracker1;
            end main
          end step;
        end parallel
        retries := retries + 1
      end while
      inform user "bring up complete"
    end main
end procedure
```

## 6–9. New language constructs

| File | What it demonstrates |
| --- | --- |
| `06_if_else.pluto` | `if … then … else … end if` and equality comparison |
| `07_case.pluto` | `case … of when V do … otherwise … end case` |
| `08_watchdog.pluto` | `watchdog on EVENT do … end on end watchdog` synchronous dispatch |
| `09_timeout.pluto` | `wait for event … with timeout T` bounded wait |
