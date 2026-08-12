import { api } from '../api';
import { Student, StudentFilterParams } from '@/types';

export const studentApi = {
  async getStudents(params?: StudentFilterParams): Promise<Student[]> {
    return api.getStudents(params);
  },

  async getStudentById(id: string): Promise<Student | null> {
    return api.getStudentById(id);
  },
};
