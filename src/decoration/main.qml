/*
    OS7 Pinstripe - KWin window decoration (Aurorae QML engine)
    SPDX-License-Identifier: GPL-3.0-only

    @UNIT@ is replaced by generate.py with the integer scale (1, 2 or 3).
    All geometry is expressed in multiples of `u` so lines stay crisp.
*/
import QtQuick
import org.kde.kwin.decoration

Decoration {
    id: root

    readonly property int u: @UNIT@
    readonly property bool active: decoration.client.active
    readonly property bool maxed: decoration.client.maximized
    // title bar: 1 outline + 17 interior + 1 separator
    readonly property int titleH: 19 * u
    // when maximized the top outline is dropped, so everything moves up by u
    readonly property int oy: maxed ? -u : 0
    // drawing area without the drop shadow
    readonly property int frameW: maxed ? width : width - u
    readonly property int frameH: maxed ? height : height - u

    alpha: true

    DecorationOptions {
        id: options
        deco: decoration
    }

    function setupBorders() {
        borders.left = u;
        borders.right = 2 * u;   // outline + shadow
        borders.bottom = 2 * u;  // outline + shadow
        borders.top = titleH;
        maximizedBorders.left = 0;
        maximizedBorders.right = 0;
        maximizedBorders.bottom = 0;
        maximizedBorders.top = titleH - u;
        // invisible grab area outside the 1 px frame, so resizing is easy
        extendedBorders.left = Math.max(6, 4 * u);
        extendedBorders.right = Math.max(6, 4 * u);
        extendedBorders.bottom = Math.max(6, 4 * u);
        extendedBorders.top = 0;
    }

    Component.onCompleted: setupBorders()

    // ---- frame ------------------------------------------------------------
    Rectangle { // offset drop shadow
        visible: !root.maxed
        x: root.u; y: root.u
        width: root.width - root.u
        height: root.height - root.u
        color: "black"
        antialiasing: false
    }
    Rectangle { // window body with 1u outline
        x: 0; y: 0
        width: root.frameW
        height: root.frameH
        color: "white"
        border.color: "black"
        border.width: root.maxed ? 0 : root.u
        antialiasing: false
    }
    Rectangle { // separator between title bar and content
        x: 0
        y: root.oy + root.titleH - root.u
        width: root.frameW
        height: root.u
        color: "black"
        antialiasing: false
    }

    // ---- title bar ----------------------------------------------------------
    Item {
        id: titleBar
        x: 0
        y: root.oy + root.u
        width: root.frameW
        height: root.titleH - 2 * root.u

        // the six pinstripes (active windows only)
        Repeater {
            model: root.active ? 6 : 0
            Rectangle {
                x: 2 * root.u
                y: (3 + 2 * index) * root.u
                width: titleBar.width - 4 * root.u
                height: root.u
                color: "black"
                antialiasing: false
            }
        }

        // white plate behind the title: exactly as wide as the text
        Rectangle {
            visible: root.active && caption.text.length > 0
            x: caption.x - 6 * root.u
            y: 0
            width: caption.width + 12 * root.u
            height: titleBar.height
            color: "white"
            antialiasing: false
        }

        Text {
            id: caption
            readonly property int leftLimit: leftGroup.x + leftGroup.width + 8 * root.u
            readonly property int rightLimit: rightGroup.x - 8 * root.u
            readonly property int available: Math.max(0, rightLimit - leftLimit)
            text: decoration.client.caption
            textFormat: Text.PlainText
            font: options.titleFont
            color: root.active ? "black" : "#808080"
            elide: Text.ElideMiddle
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            width: Math.min(implicitWidth, available)
            height: titleBar.height
            // centered on the window, but kept clear of the boxes
            x: Math.round(Math.max(leftLimit, Math.min(rightLimit - width, (titleBar.width - width) / 2)))
            y: 0
        }

        ButtonGroup {
            id: leftGroup
            x: 7 * root.u
            y: 2 * root.u
            spacing: 3 * root.u
            explicitSpacer: 8 * root.u
            buttons: options.titleButtonsLeft
            closeButton: closeComponent
            maximizeButton: maximizeComponent
            minimizeButton: minimizeComponent
            shadeButton: shadeComponent
            helpButton: plainComponent
            keepAboveButton: plainComponent
            keepBelowButton: plainComponent
            allDesktopsButton: plainComponent
            menuButton: plainComponent
            appMenuButton: plainComponent
        }

        ButtonGroup {
            id: rightGroup
            x: titleBar.width - width - 6 * root.u
            y: 2 * root.u
            spacing: 3 * root.u
            explicitSpacer: 8 * root.u
            buttons: options.titleButtonsRight
            closeButton: closeComponent
            maximizeButton: maximizeComponent
            minimizeButton: minimizeComponent
            shadeButton: shadeComponent
            helpButton: plainComponent
            keepAboveButton: plainComponent
            keepBelowButton: plainComponent
            allDesktopsButton: plainComponent
            menuButton: plainComponent
            appMenuButton: plainComponent
        }

        Component.onCompleted: decoration.installTitleItem(titleBar)
    }

    // ---- buttons ------------------------------------------------------------
    Component {
        id: closeComponent
        PinstripeButton { u: root.u; shown: root.active; buttonType: DecorationOptions.DecorationButtonClose; glyph: "close" }
    }
    Component {
        id: maximizeComponent
        PinstripeButton { u: root.u; shown: root.active; buttonType: DecorationOptions.DecorationButtonMaximizeRestore; glyph: "zoom" }
    }
    Component {
        id: minimizeComponent
        PinstripeButton { u: root.u; shown: root.active; buttonType: DecorationOptions.DecorationButtonMinimize; glyph: "collapse" }
    }
    Component {
        id: shadeComponent
        PinstripeButton { u: root.u; shown: root.active; buttonType: DecorationOptions.DecorationButtonShade; glyph: "collapse" }
    }
    Component {
        id: plainComponent
        PinstripeButton { u: root.u; shown: root.active; glyph: "" }
    }
}
