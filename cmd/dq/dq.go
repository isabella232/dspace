package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"digi.dev/dspace/client"
	"digi.dev/dspace/pkg/core"
)

// root command
var RootCmd = &cobra.Command{
	Use:   "dq [command]",
	Short: "command line dSpace client",
	Long: `
Command-line tool for managing digivice/lakes.
`,
}

// child commands
var mountCmd = &cobra.Command{
	Use:   "mount SRC TARGET [ mode ]",
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

		mt.Op = client.MOUNT

		if d, _ := cmd.Flags().GetBool("yield"); d {
			mt.Op = client.YIELD
		}

		if d, _ := cmd.Flags().GetBool("activate"); d {
			mt.Op = client.ACTIVATE
		}

		if d, _ := cmd.Flags().GetBool("delete"); d {
			mt.Op = client.UNMOUNT
		}

		if err = mt.Do(); err != nil {
			fmt.Printf("failed: %v\n", err)
			os.Exit(1)
		}
	},
}

var pipeCmd = &cobra.Command{
	Use:   "pipe [SRC TARGET] [\"d1 | d2 | ..\"]",
	Short: "Pipe a model.input.X to a model.output.Y",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		var pp *client.Piper
		var err error

		if len(args) == 1 {
			pp, err = client.NewChainPiperFromStr(args[0])
		} else {
			pp, err = client.NewPiper(args[0], args[1])
		}

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
//		// TODO invoke kubectl cli
//	},
//}
//

var (
	aliasCmd = &cobra.Command{
		Use:   "alias [ AURI ALIAS ]",
		Short: "create a model alias",
		Args:  cobra.MaximumNArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) == 0 {
				if err := client.ShowAll(); err != nil {
					fmt.Println(err)
					os.Exit(1)
				}
				os.Exit(0)
			}

			if len(args) == 1 {
				fmt.Println("args should be either none or 2")
				os.Exit(1)
			}

			// parse the auri
			auri, err := client.ParseAuri(args[0])
			if err != nil {
				fmt.Printf("unable to parse auri %s: %v\n", args[0], err)
				os.Exit(1)
			}

			a := &client.Alias{
				Auri: &auri,
				Name: args[1],
			}

			if err := a.Set(); err != nil {
				fmt.Println("unable to set alias: ", err)
				os.Exit(1)
			}
		},
	}
	aliasClearCmd = &cobra.Command{
		Use:   "clear",
		Short: "clear all aliases",
		Args:  cobra.ExactArgs(0),
		Run: func(cmd *cobra.Command, args []string) {
			if err := client.ClearAlias(); err != nil {
				fmt.Println("unable to clear alias: ", err)
				os.Exit(1)
			}
		},
	}
	aliasResolveCmd = &cobra.Command{
		Use:   "resolve ALIAS",
		Short: "resolve an alias",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := client.ResolveAndPrint(args[0]); err != nil {
				fmt.Printf("unable to resolve alias %s: %v\n", args[0], err)
				os.Exit(1)
			}
		},
	}
)

// add subcommands here
func Execute() {
	RootCmd.AddCommand(mountCmd)
	mountCmd.Flags().BoolP("delete", "d", false, "Unmount")
	mountCmd.Flags().BoolP("yield", "y", false, "Yield")
	mountCmd.Flags().BoolP("activate", "a", false, "Activate")

	RootCmd.AddCommand(pipeCmd)
	pipeCmd.Flags().BoolP("delete", "d", false, "Unpipe")

	RootCmd.AddCommand(aliasCmd)
	aliasCmd.AddCommand(aliasClearCmd)
	aliasCmd.AddCommand(aliasResolveCmd)

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
}
