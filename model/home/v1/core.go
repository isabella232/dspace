package v1

// Common values
var (
	PowerOnValue  = "on"
	PowerOffValue = "off"
	MinBrightness = 0
	MaxBrightness = 1
)

// Lamp

// Schema of the lamp model
type LampModel struct {
	Power      string `json:"power,omitempty" protobuf:"bytes,1,opt,name=power"`
	Brightness string `json:"brightness,omitempty" protobuf:"bytes,2,opt,name=brightness"`
}

// Camera
type CameraModel struct {
}

// Room

// Schema of the room model
type RoomModel struct {
	Mode       string `json:"mode,omitempty" protobuf:"bytes,1,rep,name=mode"`
	Brightness string `json:"brightness,omitempty" protobuf:"bytes,2,rep,name=brightness"`
}
