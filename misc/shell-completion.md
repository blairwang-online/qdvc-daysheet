# Shell completion (zsh)

Tab-completion for the `daysheet` command: completes the four subcommands
(`today`, `tomorrow`, `status`, `help`) with short descriptions.

This assumes **zsh** (the default shell on modern macOS), ideally with
[oh-my-zsh](https://ohmyz.sh/), though plain zsh works too.

## 1. Make the `daysheet` command available

Add an alias (or a wrapper function) to your `~/.zshrc` so the command exists:

```sh
alias daysheet='python3 /full/path/to/daysheet/daysheet.py'
```

> Completion below keys off the command name `daysheet`, so the alias name
> must match (`#compdef daysheet`).

## 2. Install the completion function

The completion lives in [`misc/_daysheet`](_daysheet). Put it somewhere on your
`fpath`.

### Option A — oh-my-zsh custom completions

```sh
mkdir -p "$ZSH_CUSTOM/completions"
ln -sf /full/path/to/daysheet/misc/_daysheet "$ZSH_CUSTOM/completions/_daysheet"
```

oh-my-zsh already adds `$ZSH_CUSTOM/completions` to `fpath`.

### Option B — plain zsh

Pick (or create) a directory and add it to `fpath` in `~/.zshrc` **before**
`compinit` runs:

```sh
mkdir -p ~/.zfunc
ln -sf /full/path/to/daysheet/misc/_daysheet ~/.zfunc/_daysheet

# in ~/.zshrc, before compinit:
fpath=(~/.zfunc $fpath)
autoload -Uz compinit && compinit
```

## 3. Reload

```sh
exec zsh
```

If completions seem stale, clear the cache and restart:

```sh
rm -f ~/.zcompdump; exec zsh
```

## Try it

```sh
daysheet <Tab>          # → today  tomorrow  status  help
daysheet to<Tab>        # → today  tomorrow
```
