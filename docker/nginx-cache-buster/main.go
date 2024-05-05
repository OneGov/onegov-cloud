// Busts parts of the nginx cache.
//
// The default cache path is '/var/cache/nginx'. All subfolders of the cache
// path are searched and any corresponding files are deleted.

// Note that the domain part of the URL is ignored, so this is equivalent to
// the example given above:

// 	nginx-cache-buster https://my-site/assets/cached.js

// The full URL would often not match anything since nginx caches by proxy
// backend and not by publicly visible URL.

// Also note that this deletes all cached resources independent of request method,
// so GET/PUT/POST etc. are all deleted.

// This CLI is meant to be run with setuid/sticky bit. That is, we run with
// root permissions under an unprivileged account. Therefore this CLI needs
// to be as minimal as possible to not expose an attack surface.
//
package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var banner = `
Usage: nginx-cache-buster /assets/cached.js --dir /var/cache/nginx

Parameters:
`

var lineURL = regexp.MustCompile(`KEY: (http|https)(GET|HEAD)(.*)`)

func mustBeADirectory(d string) {
	if i, err := os.Stat(d); err != nil {
		log.Fatalf("error reading %s: %v", i, err)
	} else if !i.IsDir() {
		log.Fatalf("not a direcrory: %s", d)
	}
}

func mustParseURLPath(u string) string {
	parsed, err := url.Parse("http://" + u)

	if err != nil {
		log.Fatalf("error parsing %s: %v", u, err)
	}

	return parsed.Path
}

func mustPassArgument(count int, name string) {
	if args := flag.NArg(); args == 0 {
		log.Fatalf("missing argument: %s", name)
	} else if args > count {
		log.Fatalf("too many arguments")
	}
}

func mustParseFlags() (directory string, dryrun bool) {
	flag.StringVar(&directory, "dir", "/var/cache/nginx", "Nginx proxy cache path")
	flag.BoolVar(&dryrun, "dry-run", false, "Dry run")

	flag.Usage = func() {
		fmt.Fprint(flag.CommandLine.Output(), banner)
		flag.PrintDefaults()
	}

	flag.Parse()

	return
}

func findLine(path string, prefix string) (string, error) {
	r, err := os.Open(path)

	if err != nil {
		return "", err
	} else {
		defer r.Close()
	}

	sc := bufio.NewScanner(r)

	for sc.Scan() {
		line := sc.Text()

		if strings.HasPrefix(line, prefix) {
			return line, nil
		}
	}

	return "", sc.Err()
}

func parseProxyLine(line string) (method, protocol, url string) {
	matches := lineURL.FindStringSubmatch(line)

	if len(matches) < 3 {
		return "", "", ""
	}

	return matches[1], matches[2], matches[3]
}

func main() {
	// disable timestamp
	log.SetFlags(0)

	// get the nginx cache directory
	directory, dryrun := mustParseFlags()
	mustBeADirectory(directory)

	// get the URL fragment
	mustPassArgument(1, "url")
	requestedURLPath := mustParseURLPath(flag.Arg(0))

	// files that are going to be deleted
	var files []string

	// walk the directories and delete matching files
	err := filepath.Walk(directory, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		// find the line starting with containing 'KEY:'
		line, err := findLine(path, "KEY:")

		if err != nil {
			return err
		}

		if line == "" {
			return nil
		}

		// it contains a method, protocol and URL
		_, _, u := parseProxyLine(line)

		if u == "" {
			return fmt.Errorf("could not parse line %s", line)
		}

		// we want only the actual path of the URL
		urlPath := mustParseURLPath(u)

		// if the path is empty we have nothing to do
		if urlPath == "" {
			return nil
		}

		// finally we can match the URL
		if strings.Contains(urlPath, requestedURLPath) {
			files = append(files, path)
		}

		return nil
	})

	// something went wrong
	if err != nil {
		log.Fatalf("error walking %s: %s", directory, err)
	}

	// delete the gathered files (or show what would be deleted)
	for _, file := range files {
		if dryrun {
			log.Printf("would delete: %s", file)
		} else {
			// the file might already have been deleted
			if _, err := os.Stat(file); !os.IsNotExist(err) {
				err := os.Remove(file)

				if err != nil {
					// the file might already have been deleted
					if !os.IsNotExist(err) {
						log.Fatalf("error deleting %s: %s", file, err)
					}
				}
			}
		}
	}
}
