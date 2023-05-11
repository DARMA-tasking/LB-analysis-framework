import vtk

mesh = vtk.vtkPolyData()
writer = vtk.vtkExodusIIWriter()
writer.SetFileName("test.ex2")
writer.SetInputData(mesh)
writer.WriteAllTimeStepsOn()
writer.Update()
