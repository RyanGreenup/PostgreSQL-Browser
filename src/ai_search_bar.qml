import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: aiSearchBar
    width: 600
    height: 40

    signal search(string query, string model)

    RowLayout {
        anchors.fill: parent
        spacing: 5

        TextField {
            id: searchBar
            Layout.fillWidth: true
            placeholderText: "Enter your AI search query..."
            onAccepted: aiSearchBar.search(text, modelCombo.currentText)
        }

        ComboBox {
            id: modelCombo
            Layout.preferredWidth: 150
            model: ["model1", "model2", "model3"] // This should be populated with actual model names
        }

        Button {
            id: searchButton
            text: "AI Search"
            onClicked: aiSearchBar.search(searchBar.text, modelCombo.currentText)
        }
    }

    function setModels(models) {
        modelCombo.model = models
    }
}
