package main

import (
	"fmt"
	"os"

	"digi.dev/digivice/client"
	"digi.dev/digivice/common"
	"github.com/spf13/cobra"
)

// root command
var RootCmd = &cobra.Command{
	Use:   "dq [ options ] [ dql ]",
	Short: "command line digivice client",
	Long: `
dq is a command-line tool for managing digivices.
`,
}

// children commands
var mountCmd = &cobra.Command{
	Use:   "mount src target [mode]",
	Short: "Mount a digivice to another digivice.",
	Args: cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var mode string
		if len(args) < 3 {
			mode = common.DefaultMode
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

// ..
// TODO: add other verbs with client-go; we currently use kubectl to do these verbs;

// add subcommands here
func Execute() {
	RootCmd.AddCommand(mountCmd)

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
}
