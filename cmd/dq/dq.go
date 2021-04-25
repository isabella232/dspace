package main

import (
	"bytes"
	"fmt"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"

	"digi.dev/dspace/client"
	"digi.dev/dspace/pkg/core"
)

// root command
var RootCmd = &cobra.Command{
	Use:   "dq [command]",
	Short: "command line dSpace client",
	Long: `
Command-line dSpace manager.
`,
}

// child commands
var mountCmd = &cobra.Command{
	Use:   "mount SRC TARGET [ mode ]",
	Short: "Mount a digivice to another digivice",
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

		//fmt.Printf("mount %s -> %s\n", mt.Source.Name, mt.Target.Name)

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
	Short: "Pipe a digilake's input.x to another's output.y",
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

		//fmt.Printf("pipe %s -> %s\n", pp.Source.Name, pp.Target.Name)

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

// XXX rely on external scripts in /mocks
// TBD support build/image/run/stop in dq
func runMake(args map[string]string, cmd string, quiet bool) error {
	cmd_ := exec.Command("make", "-s", cmd)
	cmd_.Env = os.Environ()

	for k, v := range args {
		cmd_.Env = append(cmd_.Env,
			fmt.Sprintf("%s=%s", k, v),
		)
	}

	var workDir string
	if workDir = os.Getenv("WORKDIR"); workDir == "" {
		// TBD: use the .dq's makefile
		workDir = "."
	}
	cmd_.Dir = workDir

	var out bytes.Buffer
	cmd_.Stdout = os.Stdout
	cmd_.Stdout = &out
	cmd_.Stderr = &out

	if err := cmd_.Run(); err != nil {
		log.Fatalf("error: %v\n%s", err, out.String())
		return err
	}

	if !quiet {
		fmt.Print(out.String())
	}

	if strings.Contains(
		strings.ToLower(out.String()),
		"error",
	) {
		return fmt.Errorf("%s\n", out.String())
	}

	// TBD streaming output
	//stdout, _ := cmd_.StdoutPipe()
	//_ = cmd_.Start()
	//oneRune := make([]byte, utf8.UTFMax)
	//for {
	//	count, err := stdout.Read(oneRune)
	//	if err != nil {
	//		break
	//	}
	//	fmt.Printf("%s", oneRune[:count])
	//}
	//_ = cmd_.Wait()
	return nil
}

var imageCmd = &cobra.Command{
	Use:   "image",
	Short: "List available digi images",
	Args:  cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if !q {
			fmt.Println("IMAGE ID")
		}
		_ = runMake(nil, "list", q)
	},
}

var buildCmd = &cobra.Command{
	Use:   "build KIND",
	Short: "Build a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "build", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

// XXX naive pull and push support single user/repo only
var pullCmd = &cobra.Command{
	Use:   "pull KIND",
	Short: "Pull a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "pull", q); err != nil {
			return
		}

		if err := runMake(map[string]string{
			"KIND": kind,
		}, "build", true); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var pushCmd = &cobra.Command{
	Use:   "push KIND",
	Short: "Push a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "push", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var logCmd = &cobra.Command{
	Use:     "log KIND",
	Short:   "Print log of a digi driver",
	Aliases: []string{"logs"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		name := args[0]
		if err := runMake(map[string]string{
			"NAME": name,
		}, "log", q); err == nil && !q {
		}
	},
}

var runCmd = &cobra.Command{
	Use:   "run KIND NAME",
	Short: "Run a digi given kind and name",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var c string
		if l, _ := cmd.Flags().GetBool("local"); l {
			c = "test"
		} else {
			c = "run"
		}

		kopfLog := "false"
		if k, _ := cmd.Flags().GetBool("kopf-log"); k {
			kopfLog = "true"
		}

		createAlias := true
		if noAlias, _ := cmd.Flags().GetBool("no-alias"); noAlias {
			createAlias = false
		}

		quiet, _ := cmd.Flags().GetBool("quiet")
		kind, name := args[0], args[1]
		if err := runMake(map[string]string{
			"KIND":    kind,
			"NAME":    name,
			"KOPFLOG": kopfLog,
		}, c, quiet); err == nil && !quiet {
			fmt.Println(name)

			// add alias
			if createAlias {
				var workDir string
				if workDir = os.Getenv("WORKDIR"); workDir == "" {
					workDir = "."
				}

				type gvr struct {
					Group   string `yaml:"group,omitempty"`
					Version string `yaml:"version,omitempty"`
					Kind    string `yaml:"kind,omitempty"`
				}

				raw := gvr{}
				modelFile, err := ioutil.ReadFile(filepath.Join(workDir, kind, "model.yaml"))
				if err != nil {
					log.Printf("unable to create alias, cannot open model file: %v", err)
				}

				err = yaml.Unmarshal(modelFile, &raw)
				if err != nil {
					log.Fatalf("unable to create alias, cannot unmarshal model file: %v", err)
				}

				auri := &core.Auri{
					Kind: core.Kind{
						Group:   raw.Group,
						Version: raw.Version,
						Name:    raw.Kind,
					},
					Name: name,
					// XXX use ns from cmdline option once added
					Namespace: "default",
				}
				alias := client.Alias{
					Name: name,
					Auri: auri,
				}

				if err := alias.Set(); err != nil {
					log.Fatalf("unable to create alias %v", err)
				}
			}
		}
	},
}

var stopCmd = &cobra.Command{
	Use:   "stop KIND NAME",
	Short: "Stop a digi given kind and name",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if err := runMake(map[string]string{
			"KIND": args[0],
			"NAME": args[1],
		}, "stop", q); err == nil && !q {
			fmt.Println(args[1])
		}
	},
}

var rmiCmd = &cobra.Command{
	Use:   "rmi KIND",
	Short: "Remove a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if err := runMake(map[string]string{
			"KIND": args[0],
		}, "delete", q); err == nil && !q {
			fmt.Printf("%s removed\n", args[0])
		}
	},
}

var (
	aliasCmd = &cobra.Command{
		Use:   "alias [AURI ALIAS]",
		Short: "Create a digi alias",
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
			if err := client.ResolveFromLocal(args[0]); err != nil {
				fmt.Printf("unable to resolve alias %s: %v\n", args[0], err)
				os.Exit(1)
			}
		},
	}
)

// add sub-commands here
func Execute() {
	RootCmd.AddCommand(pullCmd)
	RootCmd.AddCommand(pushCmd)
	RootCmd.AddCommand(imageCmd)
	RootCmd.AddCommand(rmiCmd)
	RootCmd.AddCommand(buildCmd)
	RootCmd.AddCommand(logCmd)
	RootCmd.AddCommand(stopCmd)

	RootCmd.AddCommand(runCmd)
	runCmd.Flags().BoolP("local", "l", false, "Run driver in local console")
	runCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")
	runCmd.Flags().BoolP("kopf-log", "k", false, "Enable kopf logging")

	RootCmd.AddCommand(mountCmd)
	mountCmd.Flags().BoolP("delete", "d", false, "Unmount source from target")
	mountCmd.Flags().BoolP("yield", "y", false, "Yield a mount")
	mountCmd.Flags().BoolP("activate", "a", false, "Activate a mount")

	RootCmd.AddCommand(pipeCmd)
	pipeCmd.Flags().BoolP("delete", "d", false, "Unpipe source from target")

	RootCmd.AddCommand(aliasCmd)
	aliasCmd.AddCommand(aliasClearCmd)
	aliasCmd.AddCommand(aliasResolveCmd)

	RootCmd.PersistentFlags().BoolP("quiet", "q", false, "Hide output")
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
}
