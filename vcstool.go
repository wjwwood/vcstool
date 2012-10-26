package main

import "fmt"
import "flag"
import "errors"

func main() {
	flag.Parse()
	if flag.NArg() == 1 {
		return errors.New("No verb passed.")
	}
	fmt.Println(flag.Arg(0))
}
