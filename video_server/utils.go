package main

import (
  "log"
  "os"
  "io/ioutil"
  "math/rand"
  "time"
  "gopkg.in/gin-gonic/gin.v1"
  "encoding/json"
  "net/http"
  "bytes"
  "sort"
  "path/filepath"
)

var (
  Info    *log.Logger
  Warn *log.Logger
  Error   *log.Logger

  killSwitches map[string]chan bool
)

func initLogging() {
  Info = log.New(os.Stdout,
    "[INFO]    ",
    log.Ldate|log.Ltime|log.Lshortfile)

  Warn = log.New(os.Stdout,
    "[WARNING] ",
    log.Ldate|log.Ltime|log.Lshortfile)

  Error = log.New(os.Stdout,
    "[ERROR]   ",
    log.Ldate|log.Ltime|log.Lshortfile)
}

func notifyTournament(returnURL string, id string, video string) {
  values := map[string]string{"key": id, "video": video}
  jsonValue, _ := json.Marshal(values)
  resp, err := http.Post(returnURL, "application/json", bytes.NewBuffer(jsonValue))
  if err != nil {
    Error.Println(err)
    return
  }
  if resp.StatusCode != http.StatusOK {
    Error.Printf("Tournament response code was %v", resp.StatusCode)
    Error.Println(resp)
  }
  Info.Println("Tournament notified successfully.")
}

func unmarshal(c *gin.Context) (data map[string]string) {
  body, err := ioutil.ReadAll(c.Request.Body)
  if err != nil {
    Error.Panicln(err)
  }
  err = json.Unmarshal(body, &data)
  if err != nil {
    Error.Panicln(err)
  }
  return
}

func panicOnError(err error) {
  if err != nil {
    Error.Panicln(err)
  }
}

func makeRandomKey() string {
  return randomString(32)
}

const letterBytes = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+="
const (
  letterIdxBits = 6                    // 6 bits to represent a letter index
  letterIdxMask = 1<<letterIdxBits - 1 // All 1-bits, as many as letterIdxBits
  letterIdxMax  = 63 / letterIdxBits
)
var src = rand.NewSource(time.Now().UnixNano())

func randomString(n int) string {
  b := make([]byte, n)

  for i, cache, remain := n-1, src.Int63(), letterIdxMax; i >= 0; {
    if remain == 0 {
      cache, remain = src.Int63(), letterIdxMax
    }
    idx := int(cache & letterIdxMask)
    b[i] = letterBytes[idx]
    i--
    cache >>= letterIdxBits
    remain--
  }
  return string(b)
}

type ByAge []os.FileInfo

func (a ByAge) Len() int           { return len(a) }
func (a ByAge) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByAge) Less(i, j int) bool { return a[i].ModTime().Unix() > a[j].ModTime().Unix() }

func keepOnlyLast(n int, folder string) {
  files, err := ioutil.ReadDir(folder)
  if err != nil {
    log.Fatal(err)
  }
  sort.Sort(ByAge(files))
  for i, file := range files {
    if i >= n {
      Info.Println("Deleting " + file.Name())
      os.Remove(filepath.Join(folder, file.Name()))
    }
  }
}
