/*
Copyright © 2020 NAME HERE <EMAIL ADDRESS>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package cmd

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	v1 "agones.dev/agones/pkg/apis/agones/v1"
	"github.com/Octops/agones-event-broadcaster/pkg/broadcaster"
	"github.com/Octops/agones-relay-http/internal/runtime"
	"github.com/Octops/agones-relay-http/internal/version"
	"github.com/Octops/agones-relay-http/pkg/broker"
	"github.com/Octops/agones-relay-http/pkg/transport"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"k8s.io/client-go/tools/clientcmd"

	homedir "github.com/mitchellh/go-homedir"
	"github.com/spf13/viper"
)

var (
	cfgFile     string
	verbose     bool
	masterURL   string
	kubeconfig  string
	syncPeriod  string
	onAddURL    string
	onUpdateURL string
	onDeleteURL string
	onEventURL  string
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "agones-relay-http",
	Short: "A brief description of your application",
	Long: `A longer description that spans multiple lines and likely contains
examples and usage of using your application. For example:

Cobra is a CLI library for Go that empowers applications.
This application is a tool to generate the needed files
to quickly create a Cobra application.`,
	// Uncomment the following line if your bare application
	// has an action associated with it:
	Run: func(cmd *cobra.Command, args []string) {
		logger := runtime.NewLogger(verbose).WithField("app", "broadcaster")
		logger.Debug(version.Info())

		cfg, err := clientcmd.BuildConfigFromFlags(masterURL, kubeconfig)
		if err != nil {
			logger.Fatalf("Error building kubeconfig: %s", err.Error())
		}

		ctx, cancel := context.WithCancel(context.Background())
		runtime.SetupSignal(cancel)

		cli, err := transport.NewClient(logger, "15s")
		if err != nil {
			logger.Fatal(err)
		}

		relayConfig := createRelayConfigFromFlags()
		bk, err := broker.NewRelayHTTP(logger, relayConfig, cli.Do)
		if err != nil {
			logger.Fatal(err)
		}

		go bk.Start(ctx)

		duration, err := time.ParseDuration(syncPeriod)
		if err != nil {
			logger.WithError(err).Fatalf("error parsing sync-period flag: %s", syncPeriod)
		}

		gsBroadcaster := broadcaster.New(cfg, bk, duration, 8090, ":9090")
		gsBroadcaster.WithWatcherFor(&v1.GameServer{})
		if err := gsBroadcaster.Build(); err != nil {
			logger.Fatal(errors.Wrap(err, "error building broadcaster"))
		}

		ctx, stop := signal.NotifyContext(context.TODO(), syscall.SIGTERM, syscall.SIGINT)
		defer stop()

		if err := gsBroadcaster.Start(ctx); err != nil {
			logger.Fatal(errors.Wrap(err, "error starting broadcaster"))
		}
	},
}

func createRelayConfigFromFlags() broker.RelayConfig {
	config := broker.RelayConfig{
		WorkerReplicas: 3, //Number of workers subscribed per queue. TODO: make it flag based
	}

	if len(onEventURL) > 0 {
		runtime.Logger().Warnf("using unique endpoints for all events: %s", onEventURL)
		config.OnAddUrl = onEventURL
		config.OnUpdateUrl = onEventURL
		config.OnDeleteUrl = onEventURL
	} else {
		config.OnAddUrl = onAddURL
		config.OnUpdateUrl = onUpdateURL
		config.OnDeleteUrl = onDeleteURL
	}

	return config
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
	cobra.OnInitialize(initConfig)

	rootCmd.Flags().StringVar(&kubeconfig, "kubeconfig", "", "set KUBECONFIG")
	rootCmd.Flags().StringVar(&masterURL, "master", "", "address of the Kubernetes API server. Overrides any value in kubeconfig. Only required if out-of-cluster.")
	rootCmd.Flags().StringVar(&syncPeriod, "sync-period", "35s", "set the minimum frequency at which watched resources are reconciled")
	rootCmd.Flags().StringVar(&onAddURL, "on-add-url", "http://localhost:8090/webhook", "list of URLs for OnAdd Events separated by comma")
	rootCmd.Flags().StringVar(&onUpdateURL, "on-update-url", "http://localhost:8090/webhook", "list of URLs for OnUpdate Events separated by comma")
	rootCmd.Flags().StringVar(&onDeleteURL, "on-delete-url", "http://localhost:8090/webhook", "list of URLs for OnDelete Events separated by comma")
	rootCmd.Flags().StringVar(&onEventURL, "on-event-url", "", "list of URLs for all kinds of Events separated by comma. If informed the other url flags will be ignored.")
	rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "enable verbose logs")
}

// initConfig reads in config file and ENV variables if set.
func initConfig() {
	if cfgFile != "" {
		// Use config file from the flag.
		viper.SetConfigFile(cfgFile)
	} else {
		// Find home directory.
		home, err := homedir.Dir()
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		// Search config in home directory with name ".agones-relay-http" (without extension).
		viper.AddConfigPath(home)
		viper.SetConfigName(".agones-relay-http")
	}

	viper.AutomaticEnv() // read in environment variables that match

	// If a config file is found, read it in.
	if err := viper.ReadInConfig(); err == nil {
		fmt.Println("Using config file:", viper.ConfigFileUsed())
	}
}
