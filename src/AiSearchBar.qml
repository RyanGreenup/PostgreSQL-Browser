import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: aiSearchBar
    width: 600
    height: 40

    property var models: []
    property string searchText: ""

    signal search(string query, string model)

    RowLayout {
        anchors.fill: parent
        spacing: 5

        TextField {
            id: searchBar
            Layout.fillWidth: true
            placeholderText: "Enter your AI search query..."
            text: aiSearchBar.searchText
            onAccepted: aiSearchBar.search(text, modelCombo.currentText)
        }

        ComboBox {
            id: modelCombo
            Layout.preferredWidth: 150
            model: aiSearchBar.models
        }

        Button {
            id: searchButton
            text: "AI Search"
            onClicked: aiSearchBar.search(searchBar.text, modelCombo.currentText)
        }
    }
}
