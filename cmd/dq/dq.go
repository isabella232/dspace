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
	Use:   "mount src target [mode] [-d]",
	Short: "Mount a digivice to another digivice.",
	Args:  cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var mode string
		if len(args) < 3 {
			mode = core.DefaultMountMode
		} else {
			mode = args[2]
		}

		mt, err := client.NewMounter(args[0], args[1], mode)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		fmt.Printf("source: %s, target: %s\n", mt.Source, mt.Target)

		f := mt.DoMount
		if d, _ := cmd.Flags().GetBool("delete"); d {
			f = mt.DoUnmount
		}
		if err = f(); err != nil {
			fmt.Printf("failed: %v\n", err)
			os.Exit(1)
		}
	},
}

var pipeCmd = &cobra.Command{
	Use:   "pipe src target [-d]",
	Short: "Pipe a model.input.X to a model.output.Y",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		pp, err := client.NewPiper(args[0], args[1])
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		fmt.Printf("source: %s, target: %s\n", pp.Source, pp.Target)

		f := pp.Pipe
		if d, _ := cmd.Flags().GetBool("delete"); d {
			f = pp.Unpipe
		}
		if err = f(); err != nil {
			fmt.Printf("pipe failed: %v\n", err)
			os.Exit(1)
		}
	},
}

//var createCmd = &cobra.Command{
//	Use:   "creat -f ",
//	Short: "create a model",
//	Args:  cobra.MinimumNArgs(2),
//	Run: func(cmd *cobra.Command, args []string) {
//		// TODO
//	},
//}
//
//var aliasCmd = &cobra.Command{
//	Use:   "alias model name",
//	Short: "create a model alias",
//	Args:  cobra.MinimumNArgs(2),
//	Run: func(cmd *cobra.Command, args []string) {
//		// TODO
//	},
//}

// add subcommands here
func Execute() {
	RootCmd.AddCommand(mountCmd)
	mountCmd.Flags().BoolP("delete", "d", false, "Unmount")

	RootCmd.AddCommand(pipeCmd)
	pipeCmd.Flags().BoolP("delete", "d", false, "Unpipe")

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
}
