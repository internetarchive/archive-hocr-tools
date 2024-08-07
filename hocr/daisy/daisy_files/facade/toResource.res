<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE resources PUBLIC "-//NISO//DTD resource 2005-1//EN" "http://www.daisy.org/z3986/2005/resource-2005-1.dtd" []>
<resources xmlns="http://www.daisy.org/z3986/2005/resource/" version="2005-1">
<!-- Default resource file for text-only DTBs. -->
<!-- Skippable structures -->
  <scope nsuri="http://www.daisy.org/z3986/2005/ncx/">
    <nodeSet id="res001" select="//smilCustomTest[@bookStruct='LINE_NUMBER']">
      <resource xml:lang="en">
        <text>Line number</text>
      </resource>
    </nodeSet>

    <nodeSet id="res002" select="//smilCustomTest[@bookStruct='NOTE']">
      <resource xml:lang="en">
        <text>Note</text>
      </resource>
    </nodeSet>

    <nodeSet id="res003" select="//smilCustomTest[@bookStruct='NOTE_REFERENCE']">
      <resource xml:lang="en">
        <text>Note reference</text>
      </resource>
    </nodeSet>

    <nodeSet id="res004" select="//smilCustomTest[@bookStruct='ANNOTATION']">
      <resource xml:lang="en">
        <text>Annotation</text>
      </resource>
    </nodeSet>

    <nodeSet id="res006" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']">
      <resource xml:lang="en">
        <text>Page</text>
      </resource>
    </nodeSet>

    <nodeSet id="res007" select="//smilCustomTest[@bookStruct='OPTIONAL_SIDEBAR']">
      <resource xml:lang="en">
        <text>Optional sidebar</text>
      </resource>
    </nodeSet>

    <nodeSet id="res008" select="//smilCustomTest[@bookStruct='OPTIONAL_PRODUCER_NOTE']">
      <resource xml:lang="en">
        <text>Optional producer note</text>
      </resource>
    </nodeSet>
  </scope>

  <scope nsuri="http://www.w3.org/2001/SMIL20/">
    <nodeSet id="res009" select="//seq[@class='note']">
      <resource xml:lang="en">
        <text>Note</text>
      </resource>
    </nodeSet>

    <nodeSet id="res010" select="//seq[@class='annotation']">
      <resource xml:lang="en">
        <text>Annotation</text>
      </resource>
    </nodeSet>

    <nodeSet id="res011" select="//seq[@class='sidebar']">
      <resource xml:lang="en">
        <text>Sidebar</text>
      </resource>
    </nodeSet>

    <nodeSet id="res012" select="//seq[@class='prodnote']">
      <resource xml:lang="en">
        <text>Producer note</text>
      </resource>
    </nodeSet>

    <nodeSet id="res013" select="//seq[@class='list']">
      <resource xml:lang="en">
        <text>List</text>
      </resource>
    </nodeSet>

    <nodeSet id="res014" select="//seq[@class='note']">
      <resource xml:lang="en">
        <text>Note</text>
      </resource>
    </nodeSet>

    <nodeSet id="res015" select="//seq[@class='table']">
      <resource xml:lang="en">
        <text>Table</text>
      </resource>
    </nodeSet>
  </scope>

</resources>