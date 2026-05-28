# Grammar reference

Every PLUTO construct currently supported by the transpiler. The full
formal grammar lives in [`src/pluto_ecss/grammar.lark`](https://github.com/stzifkas/pluto-ecss/blob/main/src/pluto_ecss/grammar.lark).

## Procedure structure

```pluto
procedure
  declare ... end declare           // optional, event declarations
  preconditions ... end preconditions  // optional
  watchdog ... end watchdog         // optional, event handlers
  main
    ...                             // required
  end main
  confirmation ... end confirmation // optional
end procedure
```

Sections may appear in any order. `main` is required; the others are optional.

## Event declarations

```pluto
declare
  event boom described by Critical failure
  event chaos2
end declare
```

Multiple events can be comma-separated or newline-separated.

## Activity calls

```pluto
initiate Switch on Star Tracker1                           // fire-and-forget
initiate and confirm Switch on Reaction Wheel3              // wait for completion
initiate and confirm Switch off Reaction Wheel3 of AOC of Satellite
```

A qualified target like `X of Y of Z` is resolved against the runtime's
system element registry.

## Steps

```pluto
initiate and confirm step BRING UP STAR TRACKER
  main
    initiate and confirm Switch on Star Tracker1;
    initiate and confirm Switch on Star Tracker2;
  end main
end step
```

## Parallel execution

```pluto
in parallel until all complete
  initiate and confirm step A
    main
      initiate and confirm Switch on Star Tracker1;
    end main
  end step;
  initiate and confirm step B
    main
      initiate and confirm Switch on Star Tracker2;
    end main
  end step;
end parallel
```

Variants:

- `in parallel until all complete … end parallel` — waits for every branch.
- `in parallel until one completes … end parallel` — returns as soon as any branch finishes.

## Control flow

```pluto
if mode = 1 then
  inform user "nominal"
else
  inform user "safe"
end if

case mode of
  when 1 do inform user "STANDBY"
  when 2 do inform user "NOMINAL"
  otherwise inform user "UNKNOWN"
end case

while c < 10 do
  c := c + 1
end while

for i := 1 to 5 do
  log "tick"
end for

repeat
  log "hi"
until done = 1
end repeat
```

## Waits and timeouts

```pluto
wait for event ready                           // blocks until raised
wait for event ready with timeout 5            // raises after 5s
wait until counter >= 3                        // poll until true
wait until temperature < 0.5 with timeout 30
```

`with timeout E` also applies to `while` and `repeat`.

## Watchdog handlers

```pluto
watchdog
  on boom do
    inform user "handling boom"
    initiate and confirm Switch off Reaction Wheel3
  end on
end watchdog
```

When `raise event boom` is reached in `main`, the corresponding handler
runs synchronously before execution continues.

## Output

```pluto
log "message"             // routed to the Python logger (visible with pluto-ecss -v)
inform user "message"     // printed to stdout
```

## Expressions

```pluto
x := 1 + 2 * 3
done := (mode = 1) and (counter > threshold)
ok := not failed
```

Operators: `+`, `-`, `*`, `/`, `=`, `<>`, `<`, `<=`, `>`, `>=`, `and`, `or`, `not`. Operands are numbers, strings (`"..."`), or qualified names.

## Assignment

```pluto
counter := 0
counter := counter + 1
```

## Comments

```pluto
// this is a line comment
```
