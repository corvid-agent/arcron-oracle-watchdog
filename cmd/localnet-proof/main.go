// Command localnet-proof reads docs/localnet.json + docs/listen.json and
// asserts docs/deploy.json still has TestNet appId 0. Offline only: no algod,
// no mnemonic, no network. Not a TestNet proof.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	root := "."
	if len(os.Args) > 1 {
		root = os.Args[1]
	}
	if err := run(root); err != nil {
		fmt.Fprintf(os.Stderr, "localnet-proof: %v\n", err)
		os.Exit(1)
	}
}

func run(root string) error {
	deploy, err := readMap(filepath.Join(root, "docs", "deploy.json"))
	if err != nil {
		return err
	}
	localnet, err := readMap(filepath.Join(root, "docs", "localnet.json"))
	if err != nil {
		return err
	}
	listen, err := readMap(filepath.Join(root, "docs", "listen.json"))
	if err != nil {
		return err
	}

	if network(deploy) != "testnet" {
		return fmt.Errorf("deploy.json network=%q want testnet", network(deploy))
	}
	if asInt(deploy["appId"]) != 0 || asInt(deploy["upkeepId"]) != 0 {
		return fmt.Errorf("deploy.json must stay appId 0 / upkeepId 0 (got appId=%v upkeepId=%v)", deploy["appId"], deploy["upkeepId"])
	}
	if network(localnet) != "localnet" || network(listen) != "localnet" {
		return fmt.Errorf("localnet/listen network must be localnet")
	}
	appID := asInt(localnet["appId"])
	mockID := asInt(listen["mockKeeperAppId"])
	if appID <= 0 || mockID <= 0 {
		return fmt.Errorf("need positive LocalNet appId and mockKeeperAppId")
	}
	if asInt(listen["appId"]) != appID {
		return fmt.Errorf("listen.appId %v != localnet.appId %d", listen["appId"], appID)
	}
	if appID == asInt(deploy["appId"]) {
		return fmt.Errorf("LocalNet appId must not equal deploy appId")
	}

	g, _ := listen["global"].(map[string]any)
	fmt.Printf(
		"LocalNet proof ok · Watchdog appId=%d mockKeeper=%d last_value=%v stale=%v watch_count=%v · TestNet deploy appId=0 (not done)\n",
		appID,
		mockID,
		g["last_value"],
		g["stale"],
		g["watch_count"],
	)
	return nil
}

func readMap(path string) (map[string]any, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var m map[string]any
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, fmt.Errorf("%s: %w", path, err)
	}
	return m, nil
}

func network(m map[string]any) string {
	s, _ := m["network"].(string)
	return s
}

func asInt(v any) int64 {
	switch n := v.(type) {
	case float64:
		return int64(n)
	case int64:
		return n
	case int:
		return int64(n)
	case json.Number:
		i, _ := n.Int64()
		return i
	default:
		return 0
	}
}
