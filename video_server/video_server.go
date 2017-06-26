package main

import (
  "os"
  "gopkg.in/gin-gonic/gin.v1"
  "path/filepath"
	"sync"
)

var mutex *sync.Mutex

func main() {
  initLogging()
  newpath := filepath.Join(".", "videos")
  os.MkdirAll(newpath, os.ModePerm)
  killSwitches = make(map[string]chan bool)
  mutex = &sync.Mutex{}
  router := gin.Default()
  router.POST("/start", start)
  router.POST("/stop", stop)
  router.GET("/status", status)
  router.Run(":8080")
}

func start(c *gin.Context) {
  data := unmarshal(c)
  streamURL := getStream(data["channel"])
  id := makeRandomKey()
  meta := metadata{
    Title: data["title"],
    Description: data["description"],
    Keywords: data["tournament_name"],
    ID: id,
    ReturnURL: data["return_url"],
  }
  mutex.Lock()
  killSwitches[id] = make(chan bool, 2)
  mutex.Unlock()
  go record("videos/" + data["title"] + ".mp4", streamURL, killSwitches[id], meta)
  c.JSON(200, gin.H{"key": id})
}

func stop(c *gin.Context) {
  data := unmarshal(c)
  id := data["id"]
  mutex.Lock()
  killSwitches[id] <- true
  close(killSwitches[id])
  delete(killSwitches, id)
  mutex.Unlock()
  c.JSON(200, gin.H{"status": "ok"})
}

func status(c *gin.Context) {
  c.JSON(200, gin.H{"status": "ok"})
}
