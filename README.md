# LC-3 Assembly Like C

## Example

write lc3asmc file like this.

``` C

at x3000 {

label:
    123
    x2333
label2:
this_address_will_never_be_used: // long label support
        R1 = R2 + R3
        R1 <- R2 & R3
        R1 += 1
        R1 += R2
        R1 = 0
        R1 = ~R2
        R1 = -R1
        R1 = 12
        return
    Mem[label] = R1
    Mem[Mem[label]] = R2
    Mem[R1] = R2
    Mem[R1 + 1] = R2
    R1 = Mem[label]
    R1 = Mem[Mem[label]]
    R1 = Mem[R1]

    goto label
    if(% > 0) goto label
    if(% < 0) goto label
    label2() // call label2
    R1()
    trap x25
    do LOOP
        do LOOP2
        R1 <- R1 + 1
        while (% > 0)
    while (% > 0)
}

```

run the following code, convert this to lc3 assembly file.

``` shell
python lc3asmc.py <asmc file> -o <output file>
```

result is shown below:

![result](./result.png)
