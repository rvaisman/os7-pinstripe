/*
    OS7 Pinstripe - title bar box (close, zoom, collapse)
    SPDX-License-Identifier: GPL-3.0-only

    13u x 13u: a 1u white margin that clears the pinstripes around an
    11u x 11u black box. Inactive windows show no boxes.
*/
import QtQuick
import org.kde.kwin.decoration

DecorationButton {
    id: button

    property int u: 1
    property bool shown: true
    property string glyph: ""   // "close", "zoom", "collapse" or "" (plain box)

    width: 13 * u
    height: 13 * u
    visible: shown && enabled

    Rectangle { // margin that interrupts the stripes
        anchors.fill: parent
        color: "white"
        antialiasing: false
    }
    Rectangle { // the box
        x: button.u; y: button.u
        width: 11 * button.u
        height: 11 * button.u
        color: button.pressed && button.glyph !== "close" ? "black" : "white"
        border.color: "black"
        border.width: button.u
        antialiasing: false
    }

    // zoom: small square in the top-left corner
    Rectangle {
        visible: button.glyph === "zoom" && !button.pressed
        x: button.u; y: button.u
        width: 7 * button.u
        height: 7 * button.u
        color: "transparent"
        border.color: "black"
        border.width: button.u
        antialiasing: false
    }

    // collapse: double horizontal line
    Repeater {
        model: button.glyph === "collapse" && !button.pressed ? 2 : 0
        Rectangle {
            x: button.u
            y: (5 + 2 * index) * button.u
            width: 11 * button.u
            height: button.u
            color: "black"
            antialiasing: false
        }
    }

    // close, pressed: the classic burst
    Repeater {
        model: button.glyph === "close" && button.pressed ? burst : []
        readonly property var burst: [
            [0, -3], [0, -2], [0, 2], [0, 3], [-3, 0], [-2, 0], [2, 0], [3, 0],
            [-3, -3], [-2, -2], [2, 2], [3, 3], [3, -3], [2, -2], [-2, 2], [-3, 3]
        ]
        Rectangle {
            x: (6 + modelData[0]) * button.u
            y: (6 + modelData[1]) * button.u
            width: button.u
            height: button.u
            color: "black"
            antialiasing: false
        }
    }
}
