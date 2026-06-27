# Shell completion (zsh + oh-my-zsh)

Tab-completion for the `daysheet` command: completes the four subcommands
(`today`, `tomorrow`, `status`, `help`) with short descriptions.

This setup assumes **zsh with [oh-my-zsh](https://ohmyz.sh/)**.

## 1. Make the `daysheet` command available

Add an alias to your `~/.zshrc` so the command exists:

```sh
daysheet() { python3 /full/path/to/daysheet/daysheet.py "$@" }
```

> The completion keys off the command name `daysheet` (`#compdef daysheet`),
> so the alias name must match.

## 2. Install the completion function

The completion lives in [`misc/_daysheet`](_daysheet). oh-my-zsh automatically
adds `$ZSH_CUSTOM/completions` to your `fpath`, so drop (or symlink) the file
there:

```sh
mkdir -p "$ZSH_CUSTOM/completions"
ln -sf /full/path/to/daysheet/misc/_daysheet "$ZSH_CUSTOM/completions/_daysheet"
```

A symlink keeps it in sync with the repo; copy it instead if you prefer.

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
