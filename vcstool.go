package main

import (
	"flag"
	"fmt"
	"github.com/wsxiaoys/terminal/color"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

var git_cmds = map[string]string{
	"pull":   "git pull",
	"diff":   "git diff",
	"status": "git status",
	"push":   "git push",
}

var hg_cmds = map[string]string{
	"pull":   "hg pull -u",
	"diff":   "hg diff",
	"status": "hg status",
	"push":   "hg push",
}

var svn_cmds = map[string]string{
	"pull":   "svn up",
	"diff":   "svn diff",
	"status": "svn status",
	"push":   "",
}

var vcs_color = map[string]string{
	"git": "g",
	"hg":  "b",
	"svn": "r",
}

var quit chan int = make(chan int)
var count int
var verb string
var (
	sequential = flag.Bool("s", false, "serializes vcs calls")
)

func execute(path string, vcs string, vcs_verb string) {
	if vcs_verb == "" {
		return
	}
	a := func(wd string, vcs string, vcs_verb string, seq bool) {
		msg := "=== @{!" + vcs_color[vcs] + "} "
		msg += filepath.Base(path)
		msg += "@| (@!" + vcs + "@|) ==="
		var cmd exec.Cmd
		cmd.Dir = wd
		cmd.Args = strings.Split(vcs_verb, " ")
		path, err := exec.LookPath(cmd.Args[0])
		if err != nil {
			path = cmd.Args[0]
		}
		cmd.Path = path
		out, err := cmd.CombinedOutput()
		if err != nil {
			br := color.Colorize("!r")
			rst := color.Colorize("|")
			fmt.Printf(color.Sprint(msg)+"\n%s\n%s%s%s\n\n", out, br, err, rst)
		} else {
			fmt.Printf(color.Sprint(msg)+"\n%s\n", out)
		}
		if !seq {
			quit <- 0
		}
	}
	if *sequential {
		a(path, vcs, vcs_verb, *sequential)
	} else {
		count += 1
		go a(path, vcs, vcs_verb, *sequential)
	}
}

func visit(path string, f os.FileInfo, err error) error {
	if f == nil || !f.IsDir() {
		return nil
	}
	entries, err := ioutil.ReadDir(path)
	if err != nil {
		log.Fatal("Failed to list the directory '", path, "': ", err)
	}
	for _, entry := range entries {
		switch {
		case entry.IsDir() && entry.Name() == ".git":
			execute(path, "git", git_cmds[verb])
			return filepath.SkipDir
		case entry.IsDir() && entry.Name() == ".hg":
			execute(path, "hg", hg_cmds[verb])
			return filepath.SkipDir
		case entry.IsDir() && entry.Name() == ".svn":
			execute(path, "svn", svn_cmds[verb])
			return filepath.SkipDir
		}
	}
	return nil
}

func main() {
	// Parse the command line arguments
	flag.Parse()

	// Make sure we got a verb
	if flag.NArg() == 0 {
		log.Fatal("No verb specified")
	}

	// I dentify the verb
	cmd := flag.Arg(0)
	switch {
	case cmd == "pull":
		verb = "pull"
	case cmd == "diff":
		verb = "diff"
	case cmd == "status", cmd == "stat", cmd == "st":
		verb = "status"
	case cmd == "push":
		verb = "push"
	default:
		log.Fatal("Invalid verb specified: ", cmd)
	}

	// Determine the working path
	path, err := os.Getwd()
	if err != nil {
		log.Fatal("Failed to get the current working directory.")
	}

	// Use the given directory if specified
	if flag.NArg() == 2 {
		path = flag.Arg(1)
	}

	// If there are more arguments, error
	if flag.NArg() > 2 {
		log.Fatal("Too many arugments")
	}

	// Walk the directory
	count = 0
	fmt.Println("Walking: ", path)
	filepath.Walk(path, visit)

	// Wait for everything to finish
	for i := 0; i < count; i++ {
		<-quit
	}
}
