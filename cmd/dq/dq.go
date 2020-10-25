package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"digi.dev/digivice/client"
	"digi.dev/digivice/pkg/core"
)

// root command
var RootCmd = &cobra.Command{
	Use:   "dq [ options ] [ dql ]",
	Short: "command line digivice client",
	Long: `
dq is a command-line tool for managing digivices.
`,
}

// child commands
var mountCmd = &cobra.Command{
	Use:   "mount src target [mode]",
	Short: "Mount a digivice to another digivice.",
	Args: cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var mode string
		if len(args) < 3 {
			mode = core.DefaultMode
		} else {
			mode = args[2]
		}

		mt, err := client.NewMounter(args[0], args[1], mode)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		fmt.Printf("try to mount %s to %s\n", mt.Source, mt.Target)
		if err = mt.Mount(); err != nil {
			fmt.Printf("mount failed: %v\n", err)
			os.Exit(1)
		}
	},
}

var pipeCmd = &cobra.Command{
	Use:   "pipe src target",
	Short: "Pipe an element.input to an element.output",
	Args: cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		pp, err := client.NewPiper(args[0], args[1])
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		fmt.Printf("try to pipe %s to %s\n", pp.Source, pp.Target)
		if err = pp.Pipe(); err != nil {
			fmt.Printf("pipe failed: %v\n", err)
			os.Exit(1)
		}
	},
}

var runCmd = &cobra.Command{
	Use:   "run src target [mode]",
	Short: "run an element.",
	Args: cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		// TODO
	},
}

// add subcommands here
func Execute() {
	RootCmd.AddCommand(mountCmd)
	RootCmd.AddCommand(pipeCmd)
	RootCmd.AddCommand(runCmd)

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
}
